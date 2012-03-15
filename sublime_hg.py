import sublime
import sublime_plugin

import os
import shlex
import threading
import functools
import subprocess

import hglib
from hglib.error import ServerError

from hg_commands import HG_COMMANDS_LIST
from hg_commands import HG_COMMANDS_AND_SHORT_HELP
from hg_commands import find_cmd
from hg_commands import AmbiguousCommandError
from hg_commands import CommandNotFoundError
from hg_commands import RUN_IN_OWN_CONSOLE
import hg_utils


VERSION = '12.3.16'


CMD_LINE_SYNTAX = 'Packages/SublimeHg/Support/SublimeHg Command Line.hidden-tmLanguage'

###############################################################################
# Globals
#------------------------------------------------------------------------------
# Holds the existing server so it doesn't have to be reloaded.
running_servers = {}
# Helps find the file where the cmdline should be restored.
recent_file_name = None
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
        if hg_utils.is_flag_set(self.command_data.flags, RUN_IN_OWN_CONSOLE):
            if sublime.platform() == 'windows':
                subprocess.Popen([self.hgs.hg_exe, self.command.encode(self.hgs.server.encoding)])
            elif sublime.platform() == 'linux':
                term = os.path.expandvars("$TERM")
                if term:
                    # At the moment, only hg serve goes this path.
                    # TODO: if port is in use, the command will fail.
                    cmd = [term, '-e', self.hgs.hg_exe, self.command]
                    subprocess.Popen(cmd)
                else:
                    sublime.status_message("SublimeHg: No terminal found.")
                    print "SublimeHg: No terminal found."
            else:
                sublime.status_message("SublimeHg: Not implemented.")
                print "SublimeHg: Not implemented. " + self.command
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

        # FIXME: some long-eunning commands block an never exit. timeout?
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
COMPLETIONS = HG_COMMANDS_LIST


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
