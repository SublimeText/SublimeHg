import sublime
import os
import contextlib


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
