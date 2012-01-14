import sublime_plugin

import os

HG_CLI_BUFFER_NAME = '__ SublimeHg Console __'
HG_CLI_PROMPT = '> '
PATH_TO_HG_CLI_SYNTAX = "Packages/SublimeHg/Support/Sublime Hg CLI.tmLanguage"

current_path = None # Dirname of latest active view (other than the console).
current_console = None # View object (SublimeHg console).


class ShowSublimeHgCli(sublime_plugin.TextCommand):
    """
    Opens and initialises the SublimeHg cli.
    """
    def is_enabled(self):
        return self.view.file_name()

    def run(self, edit):
        global current_path, current_console

        # Reuse existing console.
        if current_console:
            self.view.window().focus_view(current_console)
            return

        v = self.view.window().new_file()

        v.set_name(HG_CLI_BUFFER_NAME)
        v.set_scratch(True)
        v.set_syntax_file(PATH_TO_HG_CLI_SYNTAX)
        v.insert(edit, 0, HG_CLI_PROMPT)

        # Ensure there's a path to operate on.
        current_path = os.path.dirname(self.view.file_name())

        current_console = v


class SublimeHgSendLine(sublime_plugin.TextCommand):
    """
    Forwards the current line's text to the Mercurial command server.
    """
    def run(self, edit, cmd=None):
        global current_path
        if current_path is None:
            self.view.window().run_command('close')

        # Get line to be run and clean it.
        cmd = self.view.substr(self.view.line(self.view.sel()[0].a))
        if cmd.startswith(HG_CLI_PROMPT[0]):
            cmd = cmd[1:].strip()

        self.view.run_command('hg_command_runner', {'cmd': cmd,
                                                    'cwd': current_path,
                                                    'append': True,
                                                    'display_name': cmd})


class SublimeHgCliEventListener(sublime_plugin.EventListener):
    """
    Keeps ``current_path`` up to date with the latest virtual current
    directory.

    The SublimeHg console will always be the active view here, but Mercurial
    should operate on another view (the latest one that had a path).
    """
    def on_activated(self, view):
        # Record latest active view's path.
        if view.file_name():
            global current_path
            current_path = os.path.dirname(view.file_name())

    def on_load(self, view):
        if view.file_name():
            global current_path
            current_path = os.path.dirname(view.file_name())

    def on_close(self, view):
        global current_console
        if view.name() == HG_CLI_BUFFER_NAME:
            current_console = None
