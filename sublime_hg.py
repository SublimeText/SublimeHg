import sublime
import sublime_plugin

import threading
import functools
import subprocess
import os
import re

from shglib import commands
from shglib import utils
from shglib.commands import AmbiguousCommandError
from shglib.commands import CommandNotFoundError
from shglib.commands import find_cmd
from shglib.commands import get_commands_by_ext
from shglib.commands import HG_COMMANDS_LIST
from shglib.commands import RUN_IN_OWN_CONSOLE
from shglib.parsing import CommandLexer


VERSION = '12.8.12'


CMD_LINE_SYNTAX = 'Packages/SublimeHg/Support/SublimeHg Command Line.hidden-tmLanguage'

###############################################################################
# Globals
#------------------------------------------------------------------------------
# Holds the existing server so it doesn't have to be reloaded.
running_servers = utils.HgServers()
# Helps find the file where the cmdline should be restored.
recent_file_name = None
#==============================================================================


def run_hg_cmd(server, cmd_string):
    """Runs a Mercurial command through the given command server.
    """
    server.run_command(cmd_string)
    text, exit_code = server.receive_data()
    return text, exit_code


class KillHgServerCommand(sublime_plugin.TextCommand):
    """Shut down the server for the current file if it's running.

    The Mercurial command server does not detect state changes in the
    repo originating outside the command server itself (such as from a
    separate command line). This command makes it easy to restart the
    server so that the newest changes are picked up.
    """

    def run(self, edit):
        try:
            repo_root = utils.find_hg_root(self.view.file_name())
        # XXX: Will swallow the same error for the utils. call.
        except AttributeError:
            msg = "SublimeHg: No server found for this file."
            sublime.status_message(msg)
            return

        running_servers.shut_down(repo_root)
        sublime.status_message("SublimeHg: Killed server for '%s'" %
                               repo_root)


def run_in_console(hg_bin, cmd, encoding=None):
    if sublime.platform() == 'windows':
        cmd_str = ("%s %s && pause" % (hg_bin, cmd)).encode(encoding)
        subprocess.Popen(["cmd.exe", "/c", cmd_str,])
    elif sublime.platform() == 'linux':
        # Apparently it isn't possible to retrieve the preferred
        # terminal in a general way for different distros:
        # http://unix.stackexchange.com/questions/32547/how-to-launch-an-application-with-default-terminal-emulator-on-ubuntu
        term = utils.get_preferred_terminal()
        if term:
            cmd_str = "bash -c '%s %s;read'" % (hg_bin, cmd)
            subprocess.Popen([term, '-e', cmd_str])
        else:
            raise EnvironmentError("No terminal found."
                                   "You might want to add packages.sublime_hg.terminal "
                                   "to your settings.")
    elif sublime.platform() == 'osx':
        cmd_str = "%s %s" % (hg_bin, cmd)
        osa = "tell application \"Terminal\"\ndo script \"cd '%s' && %s\"\nactivate\nend tell" % (os.getcwd(), cmd_str)

        subprocess.Popen(["osascript", "-e", osa])
    else:
        raise NotImplementedError("Cannot run consoles on your OS: %s. Not implemented." % sublime.platform())


def escape(s, c, esc='\\\\'):
    # FIXME: won't escape \\" and such correctly.
    pat = "(?<!%s)%s" % (esc, c)
    r = re.compile(pat)
    return r.sub(esc + c, s)


class CommandRunnerWorker(threading.Thread):
    """Runs the Mercurial command and reports the output.
    """
    def __init__(self, command_server, command, view,
                 fname, display_name, append=False):
        threading.Thread.__init__(self)
        self.command_server = command_server
        self.command = command
        self.view = view
        self.fname = fname
        extensions = view.settings().get('packages.sublime_hg.extensions', [])
        self.command_data = find_cmd(extensions, display_name)[1]
        self.append = append

    def run(self):
        # The requested command interacts with remote repository or is potentially
        # long-running. We run it in its own console so it can be killed easily
        # by the user. Also, they have a chance to enter credentials if necessary.
        if utils.is_flag_set(self.command_data.flags, RUN_IN_OWN_CONSOLE):
            # FIXME: what if self.fname is None?
            target_dir = (self.fname if os.path.isdir(self.fname)
                                     else os.path.dirname(self.fname))
            with utils.pushd(target_dir):
                try:
                    run_in_console(self.command_server.hg_bin, self.command,
                                   self.command_server.encoding)
                except EnvironmentError, e:
                    sublime.status_message("SublimeHg: " + e.message)
                    print "SublimeHg: " + e.message
                except NotImplementedError, e:
                    sublime.status_message("SublimeHg: " + e.message)
                    print "SublimeHg: " + e.message
            return

        # Run the requested command through the command server.
        try:
            data, exit_code = run_hg_cmd(self.command_server, self.command)
            sublime.set_timeout(functools.partial(self.show_output, data, exit_code), 0)
        except UnicodeDecodeError, e:
            print "SublimeHg: Can't handle command string characters."
            print e
        except Exception, e:
            print "SublimeHg: Error while trying to run the command server."
            print "*" * 80
            print e
            print "*" * 80

    def show_output(self, data, exit_code):
        # If we're appending to the console, do it even if there's no data.
        if data or self.append:
            self.create_output(data, exit_code)

            # Make sure we know when to restore the cmdline later.
            global recent_file_name
            recent_file_name = self.view.file_name()
        # Just give feedback if we're running commands from the command
        # palette and there's no data.
        else:
            sublime.status_message("SublimeHg - No output.")

    def create_output(self, data, exit_code):
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
            hgs = running_servers[self.cwd]
        except utils.NoRepositoryFoundError, e:
            msg = "SublimeHg: %s" % e
            print msg
            sublime.status_message(msg)
            return
        except EnvironmentError, e:
            msg = "SublimeHg: %s (Is the Mercurial binary on your PATH?)" % e
            print msg
            sublime.status_message(msg)
            return
        except Exception, e:
            msg = ("SublimeHg: Cannot start server."
                  "(Your Mercurial version might be too old.)")
            print msg
            sublime.status_message(msg)
            return

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
    CMDS_FOR_DISPLAY = None

    def is_enabled(self):
        return self.view.file_name()

    def run(self, edit):
        if not self.CMDS_FOR_DISPLAY:
            extensions = self.view.settings().get('packages.sublime_hg.extensions', [])
            self.CMDS_FOR_DISPLAY = get_commands_by_ext(extensions)

        self.view.window().show_quick_panel(self.CMDS_FOR_DISPLAY,
                                            self.on_done)

    def on_done(self, s):
        if s == -1: return

        hg_cmd = self.CMDS_FOR_DISPLAY[s][0]
        extensions = self.view.settings().get('packages.sublime_hg.extensions', [])
        format_str , cmd_data = find_cmd(extensions, hg_cmd)

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
    """Asks the user for missing output and runs a Mercurial command.
    """
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
        self.content['input'] = escape(s, '"')
        self.view.run_command("hg_command_runner", {"cmd": self.fmtstr %
                                                                self.content})


# XXX not ideal; missing commands
COMPLETIONS = HG_COMMANDS_LIST


#_____________________________________________________________________________
class HgCompletionsProvider(sublime_plugin.EventListener):
    CACHED_COMPLETIONS = []
    CACHED_COMPLETION_PREFIXES = []
    COMPLETIONS = []

    def load_completions(self, view):
        extensions = view.settings().get('packages.sublime_hg.extensions', [])
        extensions.insert(0, 'default')
        self.COMPLETIONS = []
        for ext in extensions:
            self.COMPLETIONS.extend(commands.HG_COMMANDS[ext].keys())
        self.COMPLETIONS = set(sorted(self.COMPLETIONS))

    def on_query_completions(self, view, prefix, locations):
        # Only provide completions to the SublimeHg command line.
        if view.score_selector(0, 'source.sublime_hg_cli') == 0:
            return []

        if not self.COMPLETIONS:
            self.load_completions(view)

        # Only complete top level commands.
        current_line = view.substr(view.line(view.size()))[2:]
        if current_line != prefix:
            return []

        if prefix and prefix in self.CACHED_COMPLETION_PREFIXES:
            return self.CACHED_COMPLETIONS

        new_completions = [x for x in self.COMPLETIONS if x.startswith(prefix)]
        self.CACHED_COMPLETION_PREFIXES = [prefix] + new_completions
        self.CACHED_COMPLETIONS = zip([prefix] + new_completions,
                                                    new_completions + [prefix])
        return self.CACHED_COMPLETIONS
