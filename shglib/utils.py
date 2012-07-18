import sublime
import os
import contextlib
import client


@contextlib.contextmanager
def pushd(to):
    old_cwd = os.getcwdu()
    os.chdir(to)
    yield
    os.chdir(old_cwd)


def get_hg_exe_name():
    # todo: update this to read the view's settings instead so that it works
    # as expected with project settings, etc.
    settings = sublime.load_settings('Global.sublime-settings')
    return settings.get('packages.sublime_hg.hg_exe') or 'hg'


def get_preferred_terminal():
    settings = sublime.load_settings('Global.sublime-settings')
    return settings.get('packages.sublime_hg.terminal') or ''


def find_hg_root(path):
    # XXX check whether .hg is a dir too
    if os.path.exists(os.path.join(path, '.hg')):
        return path
    elif os.path.dirname(path) == path:
        return None
    else:
        return find_hg_root(os.path.dirname(path))


def is_flag_set(flags, which_one):
    return flags & which_one == which_one


# TODO(guillermooo): Subclass dict instead?
class HgServers(object):
    def __getitem__(self, key):
        try:
            return self._select_server(key)
        except EnvironmentError, e:
            sublime.status_message("SublimeHg: " + e.message)
            print "SublimeHg: " + e.message
            return None

    def _select_server(self, current_path=None):
        """Finds an existing server for the given path. If none is found, it
        creates one for the path.
        """
        v = sublime.active_window().active_view()
        repo_root = find_hg_root(current_path or v.file_name())
        if not repo_root:
            raise EnvironmentError("No repo found here.")
        if not repo_root in self.__dict__:
            server = self._start_server(repo_root)
            self.__dict__[repo_root] = server
        return self.__dict__[repo_root]

    def _start_server(self, repo_root):
        """Starts a new Mercurial command server.
        """
        # By default, hglib uses 'hg'. User might need to change that on
        # Windows, for example.
        hg_bin = get_hg_exe_name()
        server = client.CmdServerClient(hg_bin=hg_bin, repo_root=repo_root)
        return server
