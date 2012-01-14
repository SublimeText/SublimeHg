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


VERSION = '12.1.14'


CMD_LINE_SYNTAX = 'Packages/SublimeHg/Support/SublimeHg Command Line.hidden-tmLanguage'

###############################################################################
# Globals
#------------------------------------------------------------------------------
HISTORY_MAX_LEN = 50
PATH_TO_HISTORY = os.path.join(sublime.packages_path(), 'SublimeHg/history.txt')

# Holds the HISTORY_MAX_LEN most recently used commands from the cmdline.
history = []
# Holds the existing server so it doesn't have to be reloaded.
running_servers = {}
# Helps find the file where the cmdline should be restored.
recent_file_name = None
# Whether the user issued a command from the cmdline; restore cmdline if True.
is_interactive = False
#==============================================================================


def get_hg_exe_name():
    settings = sublime.load_settings('Global.sublime-settings')
    return settings.get('packages.sublime_hg.hg_exe') or 'hg'


def find_hg_root(path):
    # XXX check whether .hg is a dir too
    if os.path.exists(os.path.join(path, '.hg')):
        return path
    elif os.path.dirname(path) == path:
        return None
    else:
        return find_hg_root(os.path.dirname(path))


class HgCommandServer(object):
    """I drive a Mercurial command server (Mercurial>=1.9).

    For a description of the Mercurial command server see:
        * http://mercurial.selenic.com/wiki/CommandServer

    This class uses the hglib library to manage the command server.
    """
    def __init__(self, hg_exe='hg', cwd=None):
        global running_server

        # Reuse existing server or start one.
        self.cwd = cwd
        v = sublime.active_window().active_view()
        self.current_repo = find_hg_root(cwd or v.file_name())
        if not self.current_repo in running_servers:
            self.start_server(hg_exe)
        else:
            self.server = running_servers[self.current_repo]
        # running_server = self.server

    def start_server(self, hg_exe):
        # By default, hglib uses 'hg'. User might need to change that on
        # Windows, for example.
        hglib.HGPATH = hg_exe
        self.server = hglib.open(path=self.current_repo)
        global running_servers
        running_servers[self.current_repo] = self.server

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


class CommandRunnerWorker(threading.Thread):
    """Runs the Mercurial command and reports the output.
    """
    def __init__(self, hgs, command, view, fname, display_name, append=False):
        threading.Thread.__init__(self)
        self.hgs = hgs
        self.command = command
        self.view = view
        self.fname = fname
        self.command_data = HG_COMMANDS.get(display_name, None)
        self.append = append

    def run(self):
        try:
            command = self.command
            data = self.hgs.run_command(command.encode(self.hgs.server.encoding))
            sublime.set_timeout(functools.partial(self.show_output, data), 0)
        except UnicodeDecodeError, e:
            print "Oops (funny characters!)..."
            print e

    def show_output(self, data):
        # If we're appending to the console, do it even if there's no data.
        if data or self.append:
            self.create_output(data.decode(self.hgs.server.encoding))
            # Make sure we know when to restore the cmdline later.
            global recent_file_name
            recent_file_name = self.view.file_name()
        # Just give feedback if we're running commands from the command
        # palette and there's no data.
        else:
            sublime.status_message("SublimeHG - No output.")

    def create_output(self, data):
        # Output to the console or to a separate buffer.
        if not self.append:
            p = self.view.window().new_file()
            p_edit = p.begin_edit()
            p.insert(p_edit, 0, data)
            p.end_edit(p_edit)
            p.set_name("SublimeHg - Output")
            p.set_scratch(True)
            p.settings().set('gutter', False)
            if self.command_data and self.command_data.syntax_file:
                p.settings().set('gutter', True)
                p.set_syntax_file(self.command_data.syntax_file)
            p.sel().clear()
            p.sel().add(sublime.Region(0, 0))
        else:
            p = self.view
            p_edit = p.begin_edit()
            p.insert(p_edit, self.view.size(), '\n' + data + "\n> ")
            p.end_edit(p_edit)
            p.show(self.view.size())


class HgCommandRunnerCommand(sublime_plugin.TextCommand):
    def run(self, edit, cmd=None, display_name=None, cwd=None, append=False):
        self.display_name = display_name
        self.cwd = cwd
        self.append = append
        self.on_done(cmd)

    def on_done(self, s):
        # FIXME: won't work with short aliases like st, etc.
        self.display_name = self.display_name or s.split(' ')[0]

        try:
            hgs = HgCommandServer(get_hg_exe_name(), cwd=self.cwd)
        except EnvironmentError, e:
            sublime.status_message("SublimeHg:err:" + str(e))
            return
        except ServerError:
            # we can't find any repository
            sublime.status_message("SublimeHg:err: Cannot start server here.")
            return

        # FIXME: some long-running commands block an never exit. timeout?
        if getattr(self, 'worker', None) and self.worker.is_alive():
            sublime.status_message("SublimeHg: Processing another request. "
                                   "Try again later.")
            return

        self.worker = CommandRunnerWorker(hgs,
                                          s,
                                          self.view,
                                          self.cwd or self.view.file_name(),
                                          self.display_name,
                                          append=self.append,)
        self.worker.start()


class ShowSublimeHgMenuCommand(sublime_plugin.TextCommand):
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
                env.update({"caption": extra_prompt, "fmtstr": alt_cmd_name})
                self.view.run_command("hg_command_asking", env)
                return
            self.view.run_command("hg_command_runner", {"cmd": alt_cmd_name % env,
                                                  "display_name": hg_cmd})
        else:
            self.view.run_command("hg_command_runner", {"cmd": hg_cmd,
                                                  "display_name": hg_cmd})


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

        self.view.run_command("hg_command_runner", {"cmd": self.fmtstr %
                                                                self.content})

    def on_done(self, s):
        self.content['input'] = s
        self.view.run_command("hg_command_runner", {"cmd": self.fmtstr %
                                                                self.content})


# XXX not ideal; missing commands
COMPLETIONS = HG_COMMANDS_LIST + ['!h', '!mkh']


class HgCompletionsProvider(sublime_plugin.EventListener):
    CACHED_COMPLETIONS = []
    CACHED_COMPLETION_PREFIXES = []

    def on_query_completions(self, view, prefix, locations):
        # Only provide completions to the SublimeHg command line.
        if view.score_selector(0, 'source.sublime_hg_cli') == 0:
            return []

        # Only complete top level commands.
        current_line = view.substr(view.line(view.size()))[2:]
        if current_line != prefix:
            return []

        if prefix and prefix in self.CACHED_COMPLETION_PREFIXES:
            return self.CACHED_COMPLETIONS

        new_completions = [x for x in COMPLETIONS if x.startswith(prefix)]
        self.CACHED_COMPLETION_PREFIXES = [prefix] + new_completions
        self.CACHED_COMPLETIONS = zip([prefix] + new_completions,
                                                    new_completions + [prefix])
        return self.CACHED_COMPLETIONS
