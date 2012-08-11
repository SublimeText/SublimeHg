import sublime
import sublime_plugin

from sublime_hg import run_hg_cmd
from sublime_hg import running_servers


class SublimeHgDiffSelectedCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, "text.mercurial-log")

    def run(self, edit):
        if len(self.view.sel()) > 2:
            sublime.status_message("SublimeHg: Please select only two commits.")
            return

        sels = list(self.view.sel())
        if not (self.view.match_selector(sels[0].begin(), "keyword.other.changeset-ref.short.mercurial-log") and
                self.view.match_selector(sels[1].begin(), "keyword.other.changeset-ref.short.mercurial-log")):
            sublime.status_message("SublimeHg: SublimeHg: Please select only two commits.")
            return

        commit_nrs = [int(self.view.substr(x)) for x in self.view.sel()]
        older, newer = min(commit_nrs), max(commit_nrs)

        w = self.view.window()
        w.run_command("close")
        # FIXME: We're assuming this is the correct view, and it might not be.
        v = sublime.active_window().active_view()
        path = v.file_name()
        v.run_command("hg_command_runner", {"cmd": "diff -r%d:%d" % (older, newer),
                                            "display_name": "diff",
                                            "cwd": path})


class SublimeHgUpdateToRevisionCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return self.view.match_selector(0, "text.mercurial-log")

    def run(self, edit):
        if len(self.view.sel()) > 1:
            sublime.status_message("SublimeHg: Please select only one commit.")
            return

        sels = list(self.view.sel())
        if not (self.view.match_selector(sels[0].begin(), "keyword.other.changeset-ref.short.mercurial-log")):
            sublime.status_message("SublimeHg: SublimeHg: Please select only one commit.")
            return

        w = self.view.window()
        w.run_command("close")
        # FIXME: We're assuming this is the correct view, and it might not be.
        v = sublime.active_window().active_view()
        path = v.file_name()

        text, exit_code = run_hg_cmd(running_servers[path], "status")
        if text:
            msg = "SublimeHg: Don't update to a different revision with uncommited changes. Aborting."
            print msg
            sublime.status_message(msg)
            return

        v.run_command("hg_command_runner", {"cmd": "update %d" % int(self.view.substr(self.view.sel()[0])),
                                            "display_name": "update",
                                            "cwd": path})
