import sublime
import sublime_plugin

import os
import shlex
import threading
import functools

import hglib
from hglib.error import ServerError

from hg_commands import HG_COMMANDS
from hg_commands import HG_COMMANDS_LIST
from hg_commands import HG_COMMANDS_AND_SHORT_HELP


VERSION = '11.10.18b'


CMD_LINE_SYNTAX = 'Packages/SublimeHg/Support/SublimeHg Command Line.hidden-tmLanguage'

###############################################################################
# Globals
#------------------------------------------------------------------------------
HISTORY_MAX_LEN = 50
PATH_TO_HISTORY = os.path.join(sublime.packages_path(), 'SublimeHg/history.txt')

# Holds the HISTORY_MAX_LEN most recently used commands from the cmdline.
history = []
# Holds the existing server so it doesn't have to be reloaded.
running_server = None
# Helps find the file where the cmdline should be restored.
recent_file_name = None
# Whether the user issued a command from the cmdline; restore cmdline if True.
is_interactive = False
#==============================================================================


def load_history():
    global history
    if os.path.exists(PATH_TO_HISTORY):
        with open(PATH_TO_HISTORY) as fh:
            history = [ln[:-1] for ln in fh]


def make_history(append=False):
    mode = 'w' if not append else 'a'
    with open(PATH_TO_HISTORY, mode) as fh:
        fh.writelines('\n'.join(history))


def push_history(cmd):
    global history
    if cmd not in history:
        history.append(cmd)

    if len(history) > HISTORY_MAX_LEN:
        del history[0]


def find_hg_root(path):
    if os.path.exists(os.path.join(path, '.hg')):
        return path
    elif os.path.dirname(path) == path:
        return None
    else:
        return find_hg_root(os.path.dirname(path))


class HGServer(object):
    """I drive a Mercurial command server (Mercurial>=1.9).

    For a description of the Mercurial command server protocol see:
        * http://mercurial.selenic.com/wiki/CommandServer
    """
    def __init__(self, hg_exe='hg'):
        global running_server

        # Reuse existing server or start one.
        self.server = running_server
        if not running_server:
            self.start_server(hg_exe)

        running_server = self.server

    def start_server(self, hg_exe):
        # By default, hglib uses 'hg'. User might need to change that on
        # Windows, for example.
        hglib.HGPATH = hg_exe
        v = sublime.active_window().active_view()
        self.server = hglib.open(path=find_hg_root(v.file_name())
                                                            or v.file_name())

    def run_command(self, *args):
        # XXX We should probably use hglib's own utility funcs.
        if len(args) == 1 and ' ' in args[0]:
            args = shlex.split(args[0])

        if args[0] == 'hg':
            print "SublimeHg:inf: Stripped superfluous 'hg' from '%s'" % \
                                                                ' '.join(args)
            args = args[1:]
        
        print "SublimeHg:inf: Sending command '%s' as %s" % \
                                                        (' '.join(args), args)
        try:
            ret = self.server.rawcommand(args)
            return ret
        except hglib.error.CommandError, e:
            print "SublimeHg:err: " + str(e)
            return str(e)

    def shut_down(self):
        print "SublimeHg:inf: Shutting down HG server..."
        if not self.server.server.stdin.closed:
            self.server.server.stdin.close()


class CommandRunnerWorker(threading.Thread):
    def __init__(self, hgs, s, view, fname, display_name):
        threading.Thread.__init__(self)
        self.hgs = hgs
        self.s = s
        self.view = view
        self.command_data = None
        self.fname = fname
        self.command_data = HG_COMMANDS.get(display_name, None)

    def on_main_thread(self, data):
        if data:
            self.create_output_sink(data.decode(self.hgs.server.encoding))
            global recent_file_name
            recent_file_name = self.view.file_name()
        else:
            sublime.status_message("SublimeHG - No output.")
        push_history(self.s)

    def run(self):
        try:
            cmd = self.s
            repo_root = find_hg_root(os.path.dirname(self.fname))
            if repo_root:
                cmd += ' --repository "%s"' % repo_root
            data = self.hgs.run_command(cmd.encode(self.hgs.server.encoding))
            sublime.set_timeout(functools.partial(
                                                self.on_main_thread,
                                                data), 0)
        except UnicodeDecodeError, e:
            print "Oops (funny characters!)..."
            print e
            return

    def create_output_sink(self, data):
        p = self.view.window().new_file()
        p.set_name("SublimeHg - Output")
        p.set_scratch(True)
        p_edit = p.begin_edit()
        p.insert(p_edit, 0, data)
        p.end_edit(p_edit)
        p.settings().set('gutter', False)
        if self.command_data and self.command_data.syntax_file:
            p.settings().set('gutter', True)
            p.set_syntax_file(self.command_data.syntax_file)
        p.sel().clear()
        p.sel().add(sublime.Region(0, 0))


class HgCmdLineCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.file_name()

    def configure(self):
        s = sublime.load_settings('Global.sublime-settings')
        self.hg_exe = s.get('packages.sublime_hg.hg_exe') or 'hg'

    def run(self, edit, cmd=None, display_name=None):
        self.display_name = display_name
        global is_interactive
        if not cmd:
            is_interactive = True

            ip = self.view.window().show_input_panel('Hg command:',
                                                        'status',
                                                        self.on_done,
                                                        None,
                                                        None)
            ip.sel().clear()
            ip.sel().add(sublime.Region(0, ip.size()))
            ip.set_syntax_file(CMD_LINE_SYNTAX)
            # XXX If Vintage's on, the caret might look weird.
            # XXX This doesn't fix it correctly.
            ip.settings().set('command_mode', False)
            ip.settings().set('inverse_caret_state', False)
            ip.erase_status('mode')
            return

        is_interactive = False
        self.on_done(cmd)
    
    def process_intrinsic_cmds(self, cmd):
        cmd = cmd.strip()
        if cmd == '!h':
            self.view.window().show_quick_panel(history, self.repeat_history)
            return True
        elif cmd.startswith('!mkh'):
            make_history(append=(cmd.endswith('-a')))
            return True
        
    def repeat_history(self, s):
        if s == -1: return
        self.view.run_command('hg_cmd_line', {'cmd': history[s]})
    
    def on_done(self, s):
        # FIXME: won't work with short aliases like st, etc.
        self.display_name = self.display_name or s.split(' ')[0]
        # the user doesn't want anything to happen now
        if self.process_intrinsic_cmds(s): return

        if not hasattr(self, 'hg_exe'):
            self.configure()

        try:
            hgs = HGServer(self.hg_exe)
        except EnvironmentError, e:
            sublime.status_message("SublimeHg:err:" + str(e))
            return
        except ServerError:
            # we can't find any repository
            sublime.status_message("SublimeHg:err: Cannot start server here.")
            return

        if getattr(self, 'worker', None) and self.worker.is_alive():
            sublime.status_message("SublimeHg: Processing another request. "
                                   "Try again later.")
            return
        self.worker = CommandRunnerWorker(hgs,
                                            s,
                                            self.view,
                                            self.view.file_name(),
                                            self.display_name)
        self.worker.start()
            

class CmdLineRestorer(sublime_plugin.EventListener):    
    def __init__(self):
        sublime_plugin.EventListener.__init__(self)
        self.restore = False

    def on_deactivated(self, view):
        if not is_interactive:
            return
        if view.name() == 'SublimeHg - Output':
            self.restore = True
    
    def on_activated(self, view):
        if self.restore:
            view.run_command('hg_cmd_line')
            self.restore = False
    

class HgCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.file_name()

    def run(self, edit):
        self.view.window().show_quick_panel(HG_COMMANDS_AND_SHORT_HELP,
                                            self.on_done)
    
    def on_done(self, s):
        if s == -1: return

        hg_cmd = HG_COMMANDS_AND_SHORT_HELP[s][0]
        alt_cmd_name, extra_prompt = HG_COMMANDS[hg_cmd].format_str, \
                                        HG_COMMANDS[hg_cmd].prompt

        fn = self.view.file_name()
        env = {"file_name": fn}

        if alt_cmd_name:            
            if extra_prompt:
                env.update({"caption": extra_prompt, "fmtstr": alt_cmd_name,})
                self.view.run_command("hg_command_asking", env)
                return
            self.view.run_command("hg_cmd_line", {
                                                    "cmd": alt_cmd_name % env,
                                                    "display_name": hg_cmd
                                                })
        else:
            self.view.run_command("hg_cmd_line", {
                                                    "cmd": hg_cmd,
                                                    "display_name": hg_cmd
                                                })


class HgCommandAskingCommand(sublime_plugin.TextCommand):
    def run(self, edit, caption='', fmtstr='', **kwargs):
        self.fmtstr = fmtstr
        self.content = kwargs
        if caption:
            self.view.window().show_input_panel(caption,
                                                '',
                                                self.on_done,
                                                None,
                                                None)
            return
        
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr %
                                                                self.content})
    
    def on_done(self, s):
        self.content['input'] = s
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr %
                                                                self.content})


# XXX not ideal; missing commands
COMPLETIONS = HG_COMMANDS_LIST + ['!h', '!mkh']


class HgCompletionsProvider(sublime_plugin.EventListener):
    CACHED_COMPLETIONS = []
    CACHED_COMPLETION_PREFIXES = []

    def on_query_completions(self, view, prefix, locations):
        if view.score_selector(0, 'text.sublimehgcmdline') == 0:
            return []
        
        # Only complete top level commands.
        if view.substr(sublime.Region(0, view.size())) != prefix:
            return []
        
        if prefix and prefix in self.CACHED_COMPLETION_PREFIXES:
            return self.CACHED_COMPLETIONS

        compls = [x for x in COMPLETIONS if x.startswith(prefix)]
        self.CACHED_COMPLETION_PREFIXES = [prefix] + compls
        self.CACHED_COMPLETIONS = zip([prefix] + compls, compls + [prefix])
        return self.CACHED_COMPLETIONS


# Load history if it exists
load_history()
