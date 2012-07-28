import sublime_plugin

import os


CLI_BUFFER_NAME = '==| SublimeHg Console |=='
CLI_PROMPT = '> '
CLI_SYNTAX_FILE = 'Packages/SublimeHg/Support/Sublime Hg CLI.hidden-tmLanguage'

current_path = None # Dirname of latest active view (other than the console).
existing_console = None # View object (SublimeHg console).


class ShowSublimeHgCli(sublime_plugin.TextCommand):
    """
    Opens and initialises the SublimeHg cli.
    """
    def is_enabled(self):
        # Do not show if the file does not have a known path. SublimeHg would
        # not be able to find the corresponding root repo for it.
        return self.view.file_name()

    def init_console(self):
        v = self.view.window().new_file()
        v.set_name(CLI_BUFFER_NAME)
        v.set_scratch(True)
        v.set_syntax_file(CLI_SYNTAX_FILE)
        edit = v.begin_edit()
        v.insert(edit, 0, CLI_PROMPT)
        v.end_edit(edit)

        return v

    def run(self, edit):
        global current_path, existing_console

        # Ensure there's a path to operate on. At the time this executes, we
        # assume the active view is the one the user wants to operate on
        # (because it's the one he's lookign at).
        current_path = os.path.dirname(self.view.file_name())

        # Reuse existing console. existing_console will not work across sessions,
        # even if you leave a console open.
        if existing_console:
            self.view.window().focus_view(existing_console)
            if self.view.window().active_view().name() == CLI_BUFFER_NAME:
                return

        # Close "dead" consoles. There might be others open from a previous
        # session.
        for v in self.view.window().views():
            if v.name() == CLI_BUFFER_NAME:
                self.view.window().focus_view(v)
                self.view.window().run_command('close')

        existing_console = self.init_console()


class SublimeHgSendLine(sublime_plugin.TextCommand):
    """
    Forwards the current line's text to the Mercurial command server.
    """
    def append_chars(self, s):
        edit = self.view.begin_edit()
        self.view.insert(edit, self.view.size(), s)
        self.view.end_edit(edit)

    def new_line(self):
        self.append_chars("\n")

    def write_prompt(self):
        self.new_line()
        self.append_chars(CLI_PROMPT)

    def append_output(self, output):
        self.new_line()
        self.append_chars(output)

    def run(self, edit, cmd=None):
        global current_path
        if current_path is None:
            self.view.window().run_command('close')

        # Get line to be run and clean it.
        cmd = self.view.substr(self.view.line(self.view.sel()[0].a))
        if cmd.startswith(CLI_PROMPT[0]):
            cmd = cmd[1:].strip()

        params = dict(cmd=cmd, cwd=current_path, append=True,
                      # send only first token (for command search)
                      display_name=cmd.split()[0])
        self.view.run_command('hg_command_runner', params)


class SublimeHgCliEventListener(sublime_plugin.EventListener):
    """
    Ensures global state remains consistent.

    The SublimeHg console will always be the active view here, but Mercurial
    should operate on another view (the latest one that had a path).
    """
    def record_path(self, view):
        # We're only interested in files that do have a path, so we can
        # record it.
        if view.file_name():
            global current_path
            current_path = os.path.dirname(view.file_name())

    def on_activated(self, view):
        self.record_path(view)

    def on_load(self, view):
        self.record_path(view)

    def on_close(self, view):
        global existing_console
        if view.name() == CLI_BUFFER_NAME:
            existing_console = None
