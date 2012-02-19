import sublime
import sublime_plugin

import os
import shlex
import threading
import functools
import subprocess
import re

import hglib
from hglib.error import ServerError

from hg_commands import HG_COMMANDS_LIST
from hg_commands import HG_COMMANDS_AND_SHORT_HELP
from hg_commands import find_cmd
from hg_commands import AmbiguousCommandError
from hg_commands import CommandNotFoundError
from hg_commands import EDIT_COMMIT_MESSAGE
from hg_commands import SEPARATE_PROCESS
import hg_utils


VERSION = '12.2.19'


CMD_LINE_SYNTAX = 'Packages/SublimeHg/Support/SublimeHg Command Line.hidden-tmLanguage'
INPUT_BUFFER_NAME = '==| SublimeHg User Input |=='

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


class HgCommandServer(object):
    """I drive a Mercurial command server (Mercurial>=1.9).

    For a description of the Mercurial command server see:
        * http://mercurial.selenic.com/wiki/CommandServer

    This class uses the hglib library to manage the command server.
    """
    def __init__(self, hg_exe='hg', cwd=None):
        global running_server

        # Reuse existing server or start one.
        self.hg_exe = hg_exe
        self.cwd = cwd
        v = sublime.active_window().active_view()
        self.current_repo = hg_utils.find_hg_root(cwd or v.file_name())
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
        self.command_data = find_cmd(display_name)[1]

        self.append = append

    def run(self):
        if hg_utils.is_flag_set(self.command_data.flags, SEPARATE_PROCESS):
            subprocess.Popen([self.hgs.hg_exe, self.command.encode(self.hgs.server.encoding)])
            return
        try:
            command = self.command
            data = self.hgs.run_command(command.encode(self.hgs.server.encoding))
            sublime.set_timeout(functools.partial(self.show_output, data), 0)
        except UnicodeDecodeError, e:
            print "SublimeHg: Can't handle command string characters."
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
            sublime.status_message("SublimeHg - No output.")

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
        try:
            self.on_done(cmd)
        except CommandNotFoundError:
            # This will happen when we cannot find an unambiguous command or
            # any command at all.
            sublime.status_message("SublimeHg: Command not found.")
        except AmbiguousCommandError:
            sublime.status_message("SublimeHg: Ambiguous command.")

    def on_done(self, s):
        # FIXME: won't work with short aliases like st, etc.
        self.display_name = self.display_name or s.split(' ')[0]

        try:
            hgs = HgCommandServer(hg_utils.get_hg_exe_name(), cwd=self.cwd)
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
        format_str , cmd_data = find_cmd(hg_cmd)

        fn = self.view.file_name()
        env = {'file_name': fn}

        # Handle commands differently whether they require input or not.
        # Commands requiring input have a "format_str".
        if format_str:
            # Collect single-line inputs from an input panel.
            if '%(input)s' in format_str:
                env['caption'] = cmd_data.prompt
                env['fmtstr'] = format_str
                self.view.run_command('hg_command_asking', env)
                return
            # Handle requests for longer inputs either from a buffer or through
            # the HGEDITOR, depending on the user's preference.
            elif (not hg_utils.use_hg_editor() and
                  # shlex doesn't support Unicode before Python 2.7.3, so use regexes.
                  re.search(r'(?:-e|--edit)\b', format_str)):

                # If the user requests editing the existing commit message, we
                # need to retrieve it first.
                if (hg_utils.is_flag_set(cmd_data.flags, EDIT_COMMIT_MESSAGE) and
                    re.search(r'(?:-e|--edit)\b', format_str)):

                    current_repo = hg_utils.find_hg_root(self.view.file_name())
                    # This way of retrieving the existing commit message doesn't
                    # seem to be particulary elegant or robust, but the Mercurial
                    # API is unstable according to their own docs.
                    msg = running_servers[current_repo].rawcommand(['-v', 'parent'])
                    _, _, msg = msg.partition('description:')
                    env.update({'default_message': msg.strip()})

                env.update({'caption': cmd_data.prompt,
                            'fmtstr': format_str})
                self.view.run_command('hg_command_asking_in_buffer', env)
                return
            # Command requires additional info, but it's provided automatically.
            self.view.run_command('hg_command_runner', {
                                              'cmd': format_str % env,
                                              'display_name': hg_cmd})
        else:
            # It's a simple command that doesn't require any input, so just
            # go ahead and run it.
            self.view.run_command('hg_command_runner', {
                                              'cmd': hg_cmd,
                                              'display_name': hg_cmd})


class BufferInputEventListener(sublime_plugin.EventListener):
    def on_close(self, view):
        try:
            if view.name() == INPUT_BUFFER_NAME:
                user_input = view.substr(sublime.Region(0, view.size()))
                if user_input.strip():
                    HgCommandAskingInBufferCommand.last_content['input'] = user_input
                    sublime.active_window().run_command('prev_view_in_stack')
                    if sublime.active_window().active_view().name() == CLI_BUFFER_NAME:
                        sublime.active_window().run_command('prev_view_in_stack')
                        # sublime.active_window().run_command('close')
                    view.run_command('hg_command_runner', {
                                        'cmd': HgCommandAskingInBufferCommand.last_format_str % \
                                               HgCommandAskingInBufferCommand.last_content
                        })
                else:
                    # user provided empty message
                    sublime.status_message("SublimeHg: Aborted - Nothing happened.")
        finally:
            # Clean up after ourselves.
            HgCommandAskingInBufferCommand.last_content = None
            HgCommandAskingInBufferCommand.last_format_str = None


class HgCommandAskingInBufferCommand(sublime_plugin.TextCommand):
    last_content = None
    last_format_str = None
    def run(self, edit, caption='', fmtstr='', **kwargs):
        self.fmtstr = fmtstr
        self.content = kwargs
        if caption:
            if re.search(r'(?:-e|--edit)\b', self.fmtstr):
                self.fmtstr = re.sub(r'(?:-e|--edit)\b', '', self.fmtstr)
                self.fmtstr += ' -m "%(input)s"'
            HgCommandAskingInBufferCommand.last_content = self.content
            HgCommandAskingInBufferCommand.last_format_str = self.fmtstr
            v = self.view.window().new_file()
            v.set_name(INPUT_BUFFER_NAME)
            v.insert(edit, 0, kwargs.get('default_message', ''))
            v.set_scratch(True)
            return

        kwargs["cmd"] = self.fmtstr % self.content
        self.view.run_command("hg_command_runner", kwargs)


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


# Avoid circular import.
from sublime_hg_cli import CLI_BUFFER_NAME
