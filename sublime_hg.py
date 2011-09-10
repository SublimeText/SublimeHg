import sublime
import sublime_plugin

import os
import shlex

import hglib


VERSION = '11.9.10'

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


class HGServer(object):
    """I drive a Mercurial command server (Mercurial>=1.9).

    Mercurial command server protocol: http://mercurial.selenic.com/wiki/CommandServer
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
        self.server = hglib.open()

    def run_command(self, *args):
        # XXX We should probably use hglib's own utility funcs.
        if len(args) == 1 and ' ' in args[0]:
            args = shlex.split(args[0])

        if args[0] == 'hg':
            print "SublimeHg:inf: Stripped superfluous 'hg' from '%s'" % ' '.join(args)
            args = args[1:]
        
        print "SublimeHg:inf: Sending command '%s' as %s" % (' '.join(args), args)
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


class HgCmdLineCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.file_name()

    def configure(self):
        s = sublime.load_settings('Global.sublime-settings')
        self.hg_exe = s.get('packages.sublime_hg.hg_exe') or 'hg'

    def run(self, edit, cmd=None):
        global is_interactive
        if not cmd:
            is_interactive = True

            ip = self.view.window().show_input_panel('Hg command:', 'status', self.on_done, None, None)
            ip.sel().clear()
            ip.sel().add(sublime.Region(0, ip.size()))
            ip.set_syntax_file('Packages/SublimeHg/Support/SublimeHg Command Line.tmLanguage')
            # XXX If Vintage's on, the caret might look weird.
            # XXX This doesn't fix it correctly.
            ip.settings().set('command_mode', False)
            ip.settings().set('inverse_caret_state', False)
            ip.erase_status('mode')
            return

        is_interactive = False
        self.on_done(cmd)
    
    def create_output_sink(self, data, is_diff=False):
        p = self.view.window().new_file()
        p.set_name("SublimeHg - Output")
        p.set_scratch(True)
        p_edit = p.begin_edit()
        p.insert(p_edit, 0, data)
        p.end_edit(p_edit)
        p.settings().set('gutter', False)
        if is_diff:
            p.settings().set('gutter', True)
            p.set_syntax_file('Packages/Diff/Diff.tmLanguage')
    
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
        # the user doesn't want anything to happen now
        if self.process_intrinsic_cmds(s): return

        old_cd = os.getcwd()
        os.chdir(os.path.dirname(self.view.file_name()))

        if not hasattr(self, 'hg_exe'):
            self.configure()

        try:
            hgs = HGServer(self.hg_exe)
        except EnvironmentError, e:
            sublime.status_message("SublimeHg:err:" + str(e))
            os.chdir(old_cd)
            return

        try:
            data = hgs.run_command(s.encode(hgs.server.encoding))
            if data:
                self.create_output_sink(data.decode(hgs.server.encoding), 'diff' in s.lower())
                global recent_file_name
                recent_file_name = self.view.file_name()
            else:
                sublime.status_message("SublimeHG - No output.")
                if is_interactive:
                    ip = self.view.window().show_input_panel('Hg command:', '', self.on_done, None, None)
                    ip.set_syntax_file('Packages/SublimeHg/Support/SublimeHg Command Line.tmLanguage')
        except UnicodeDecodeError, e:
            print "Oops (funny characters!)..."
            print e
            return
        finally:
            os.chdir(old_cd)
        
        push_history(s)
            
class CmdLineRestorer(sublime_plugin.EventListener):    
    def on_activated(self, view):
        global recent_file_name
        global is_interactive
        if not is_interactive: return
        if not recent_file_name: return
        if view.file_name() == recent_file_name:
            recent_file_name = None
            view.run_command('hg_cmd_line')
    
# TODO: Add serve and start in a separate process?
SUBLIMEHG_CMDS = {
    # Used named tuples
    "add": ['', None],
    "add (this file)": ['add "%(file_name)s"', None],
    "addremove": ['', None],
    "annotate (this file)": ['annotate "%(file_name)s"', None],
    # "archive", # Too complicated for this simple interface?
    # "backout", # Too complicated for this simple interface?
    # "bisect", # Too complicated for this simple interface?
    "bookmark (parent revision)...": ['bookmark "%(input)s"', 'Bookmark name:'],
    "bookmarks": ['', None],
    "branch": ['', None],
    "branches": ['', None],
    # "bundle",
    # "cat",
    # "clone",
    "commit...": ['commit -m "%(input)s"', 'Commit message:'],
    "commit (this file)...": ['commit "%(file_name)s" -m "%(input)s"', "Commit message:"],
    # "copy",
    "diff": ['', None],
    "diff (this file)": ['diff "%(file_name)s"', None],
    # "export",
    "forget (this file)": ['forget "%(file_name)s"', None],
    "grep...": ['grep "%(input)s"', 'Pattern (grep):'] ,
    "heads": ['heads', None],
    "help": ['', None],
    "help...": ['help %(input)s', 'Help topic:'],
    "identify": ['', None],
    # "import",
    "incoming": ['', None],
    # "init",
    "locate...": ['locate "%(input)s"', 'Pattern (locate):'],
    "log": ['', None],
    "log (this file)": ['log "%(file_name)s"', None],
    "manifest": ['', None],
    "merge": ['', None],
    "merge...": ['merge "%(input)s"', "Revision to merge with:"],
    "outgoing": ['', None],
    "parents": ['', None],
    "paths": ['', None],
    "pull": ['', None],
    "push": ['', None],
    "push...": ['push "%(input)s"', "Push target:"],
    "recover": ['', None],
    "remove (this file)...": ['remove "%(input)s"', None],
    "rename (this file)...": ['rename "%(file_name)s" "%(input)s"', "New name:"],
    "resolve (this file)": ['resolve "%(file_name)s"', None],
    "revert (this file)": ['revert "%(file_name)s"', None],
    "rollback": ['', None],
    "root": ['', None],
    "showconfig": ['', None],
    "status": ['', None],
    "status (this file)": ['status "%(file_name)s"', None],
    "summary": ['', None],
    "tag...": ['tag "%(input)s"', "Tag name:"],
    "tags": ['', None],
    "tip": ['', None],
    # "unbundle",
    "update": ['', None],
    "update...": ['update "%(input)s"', "Branch:"],
    "verify": ['', None],
    "version": ['', None]
    }


# At some point we'll let the user choose whether to load extensions.
if True:
    MQ_CMDS = {
        "qapplied": ['qapplied -s', None],
        "qdiff": ['', None],
        "qgoto...": ['qgoto "%(input)s"', "Patch name:"],
        "qheader": ['', None],
        "qheader...": ['qheader "%(input)s"', "Patch name:"],
        "qnext": ['qnext -s', None],
        "qpop": ['', None],
        "qprev": ['qprev -s', None],
        "qpush": ['', None],
        "qrefresh": ['', None],
        "qrefresh... (EDIT commit message)": ['qrefresh -e', None],
        "qrefresh... (NEW commit message)": ['qrefresh -m "%(input)s"', "Commit message:"],
        "qseries": ['qseries -s', None],
        "qfinish...": ['qfinish "%(input)s"', 'Patch name:'],
        "qnew...": ['qnew "%(input)s"', 'Patch name:'],
        "qtop": ['qtop -s', None],
        "qunapplied": ['', None],
    } 

    SUBLIMEHG_CMDS.update(MQ_CMDS)


class HgCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.file_name()

    def run(self, edit):
        self.view.window().show_quick_panel(sorted(SUBLIMEHG_CMDS.keys()),
                                                                self.on_done)
    
    def on_done(self, s):
        if s == -1: return

        hg_cmd = sorted(SUBLIMEHG_CMDS.keys())[s]
        alt_cmd_name, extra_prompt = SUBLIMEHG_CMDS[hg_cmd]

        fn = self.view.file_name()
        env = {"file_name": fn}

        if alt_cmd_name:            
            if extra_prompt:
                env.update({"caption": extra_prompt, "fmtstr": alt_cmd_name,})
                self.view.run_command("hg_command_asking", env)
                return
            self.view.run_command("hg_cmd_line", {"cmd": alt_cmd_name % env})
        else:
            self.view.run_command("hg_cmd_line", {"cmd": hg_cmd})


class HgCommandAskingCommand(sublime_plugin.TextCommand):
    def run(self, edit, caption='', fmtstr='', **kwargs):
        self.fmtstr = fmtstr
        self.content = kwargs
        if caption:
            self.view.window().show_input_panel(caption, '', self.on_done, None, None)
            return
        
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr % self.content})
    
    def on_done(self, s):
        self.content['input'] = s
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr % self.content})


# XXX not ideal; missing commands
COMPLETIONS = sorted(SUBLIMEHG_CMDS.keys() + ['!h', '!mkh'])
COMPLETIONS = list(set([x.replace('.', '') for x in COMPLETIONS if ' ' not in x]))


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
