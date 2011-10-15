from collections import namedtuple


cmd_data = namedtuple('cmd_data','format_str prompt enabled syntax_file')

HG_COMMANDS = {
    'status': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'commit...': cmd_data(
                    format_str='commit -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True,
                    syntax_file='',
                    ),
    'add': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'add (this file)': cmd_data(
                    format_str='add "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'addremove': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'annotate (this file)': cmd_data(
                    format_str='annotate "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Annotate.hidden-tmLanguage',
                    ),
    'bookmark (parent revision)': cmd_data(
                    format_str='bookmark "%(input)s"',
                    prompt='Bookmark name:',
                    enabled=True,
                    syntax_file='',
                    ),
    'bookmarks': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'branch': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'branches': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'commit (this file)': cmd_data(
                    format_str='commit "%(file_name)s" -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True,
                    syntax_file='',
                    ),
    'diff': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/Diff/Diff.tmLanguage',
                    ),
    'diff (this file)': cmd_data(
                    format_str='diff "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/Diff/Diff.tmLanguage',
                    ),
    'forget (this file)': cmd_data(
                    format_str='forget "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'grep...': cmd_data(
                    format_str='grep "%(input)s"',
                    prompt='Pattern (grep):',
                    enabled=True,
                    syntax_file='',
                    ),
    'heads': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'help': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'help...': cmd_data(
                    format_str='help "%(input)s"',
                    prompt='Help topic:',
                    enabled=True,
                    syntax_file='',
                    ),
    'indentify': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'incoming': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'locate...': cmd_data(
                    format_str='locate "%(input)s"',
                    prompt='Pattern:',
                    enabled=True,
                    syntax_file='',
                    ),
    'log': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    ),
    'log (this file)': cmd_data(
                    format_str='log "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    ),
    'manifest': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'merge': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'merge...': cmd_data(
                    format_str='merge "%(input)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'outgoing': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    ),
    'parents': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'pull': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    'push': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "push...": cmd_data(
                    format_str='push "%(input)s"',
                    prompt="Push target:",
                    enabled=True,
                    syntax_file='',
                    ),
    "recover": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "remove (this file)...": cmd_data(
                    format_str='remove "%(input)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "rename (this file)...": cmd_data(
                    format_str='rename "%(file_name)s" "%(input)s"',
                    prompt="New name:",
                    enabled=True,
                    syntax_file='',
                    ),
    "resolve (this file)": cmd_data(
                    format_str='resolve "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "revert (this file)": cmd_data(
                    format_str='revert "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "rollback": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "root": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "showconfig": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "status": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Status Report.hidden-tmLanguage',
                    ),
    "status (this file)": cmd_data(
                    format_str='status "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Status Report.hidden-tmLanguage',
                    ),
    "summary": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "tag...": cmd_data(
                    format_str='tag "%(input)s"',
                    prompt="Tag name:",
                    enabled=True,
                    syntax_file='',
                    ),
    "tags": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "tip": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "update": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "update...": cmd_data(
                    format_str='update "%(input)s"',
                    prompt="Branch:",
                    enabled=True,
                    syntax_file='',
                    ),
    "verify": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
    "version": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    ),
}

# At some point we'll let the user choose whether to load extensions.
if True:
    MQ_CMDS = {
        "qapplied": cmd_data(
                        format_str='qapplied -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qdiff": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='Packages/Diff/Diff.tmLanguage',
                        ),
        "qgoto...": cmd_data(
                        format_str='qgoto "%(input)s"',
                        prompt="Patch name:",
                        enabled=True,
                        syntax_file='',
                        ),
        "qheader": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qheader...": cmd_data(
                        format_str='qheader "%(input)s"',
                        prompt="Patch name:",
                        enabled=True,
                        syntax_file='',
                        ),
        "qnext": cmd_data(
                        format_str='qnext -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qpop": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qprev": cmd_data(
                        format_str='qprev -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qpush": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qrefresh": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qrefresh... (EDIT commit message)": cmd_data(
                        format_str='qrefresh -e',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qrefresh... (NEW commit message)": cmd_data(
                        format_str='qrefresh -m "%(input)s"',
                        prompt="Commit message:",
                        enabled=True,
                        syntax_file='',
                        ),
        "qseries": cmd_data(
                        format_str='qseries -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qfinish...": cmd_data(
                        format_str='qfinish "%(input)s"',
                        prompt='Patch name:',
                        enabled=True,
                        syntax_file='',
                        ),
        "qnew...": cmd_data(
                        format_str='qnew "%(input)s"',
                        prompt='Patch name:',
                        enabled=True,
                        syntax_file='',
                        ),
        "qtop": cmd_data(
                        format_str='qtop -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
        "qunapplied": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        ),
    } 


    HG_COMMANDS.update(MQ_CMDS)

HG_COMMANDS_LIST = [x.replace('.', '') for x in HG_COMMANDS if ' ' not in x]
HG_COMMANDS_LIST = list(sorted(set(HG_COMMANDS_LIST)))


def find_command(prefix):
    hits = [x for x in HG_COMMANDS_LIST if x.startswith(prefix)]
    if len(hits) == 1:
        return hits[0]


if __name__ == '__main__':
    print HG_COMMANDS
    print HG_COMMANDS_LIST

    print find_command('st')
    print find_command('s')
    print find_command('qu')
