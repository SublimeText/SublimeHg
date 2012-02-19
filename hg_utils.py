import sublime
import os


def get_hg_exe_name():
    settings = sublime.load_settings('Global.sublime-settings')
    return settings.get('packages.sublime_hg.hg_exe') or 'hg'


def use_hg_editor():
    return sublime.load_settings(
                'SublimeHg.sublime-settings').get('use_hg_editor', False)


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
