from collections import namedtuple


cmd_data = namedtuple('cmd_data','format_str prompt enabled syntax_file help')

HG_COMMANDS = {
    'commit...': cmd_data(
                    format_str='commit -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True,
                    syntax_file='',
                    help='commit the specified files or all outstanding changes',
                    ),
    'add': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='add the specified files on the next commit',
                    ),
    'add (this file)': cmd_data(
                    format_str='add "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='add the specified files on the next commit',
                    ),
    'addremove': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='add all new files, delete all missing files',
                    ),
    'annotate (this file)': cmd_data(
                    format_str='annotate "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Annotate.hidden-tmLanguage',
                    help='show changeset information by line for each file',
                    ),
    'blame (this file)': cmd_data(
                    format_str='annotate "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Annotate.hidden-tmLanguage',
                    help='show changeset information by line for each file',
                    ),
    'bookmark (parent revision)': cmd_data(
                    format_str='bookmark "%(input)s"',
                    prompt='Bookmark name:',
                    enabled=True,
                    syntax_file='',
                    help='track a line of development with movable markers',
                    ),
    'bookmarks': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='track a line of development with movable markers',
                    ),
    'branch': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='set or show the current branch name',
                    ),
    'branches': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='list repository named branches',
                    ),
    'commit (this file)': cmd_data(
                    format_str='commit "%(file_name)s" -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True,
                    syntax_file='',
                    help='commit the specified files or all outstanding changes',
                    ),
    'diff': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/Diff/Diff.tmLanguage',
                    help='diff repository (or selected files)',
                    ),
    'diff (this file)': cmd_data(
                    format_str='diff "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/Diff/Diff.tmLanguage',
                    help='diff repository (or selected files)',
                    ),
    'forget (this file)': cmd_data(
                    format_str='forget "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='forget the specified files on the next commit',
                    ),
    'grep...': cmd_data(
                    format_str='grep "%(input)s"',
                    prompt='Pattern (grep):',
                    enabled=True,
                    syntax_file='',
                    help='search for a pattern in specified files and revisions',
                    ),
    'heads': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show current repository heads or show branch heads',
                    ),
    'help': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show help for a given topic or a help overview',
                    ),
    'help...': cmd_data(
                    format_str='help "%(input)s"',
                    prompt='Help topic:',
                    enabled=True,
                    syntax_file='',
                    help='show help for a given topic or a help overview',
                    ),
    'indentify': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='identify the working copy or specified revision',
                    ),
    'incoming': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show new changesets found in source',
                    ),
    'locate...': cmd_data(
                    format_str='locate "%(input)s"',
                    prompt='Pattern:',
                    enabled=True,
                    syntax_file='',
                    help='locate files matching specific patterns',
                    ),
    'log': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    help='show revision history of entire repository or files',
                    ),
    'log (this file)': cmd_data(
                    format_str='log "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    help='show revision history of entire repository or files',
                    ),
    'manifest': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='output the current or given revision of the project manifest',
                    ),
    'merge': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='merge working directory with another revision',
                    ),
    'merge...': cmd_data(
                    format_str='merge "%(input)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='merge working directory with another revision',
                    ),
    'outgoing': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Log.hidden-tmLanguage',
                    help='show changesets not found in the destination',
                    ),
    'parents': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show the parents of the working directory or revision',
                    ),
    'paths': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show aliases for remote repositories',
                    ),
    'pull': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='pull changes from the specified source',
                    ),
    'push': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='push changes to the specified destination',
                    ),
    "push...": cmd_data(
                    format_str='push "%(input)s"',
                    prompt="Push target:",
                    enabled=True,
                    syntax_file='',
                    help='push changes to the specified destination',
                    ),
    "recover": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='roll back an interrupted transaction',
                    ),
    "remove (this file)...": cmd_data(
                    format_str='remove "%(input)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='remove the specified files on the next commit',
                    ),
    "rename (this file)...": cmd_data(
                    format_str='rename "%(file_name)s" "%(input)s"',
                    prompt="New name:",
                    enabled=True,
                    syntax_file='',
                    help='rename files; equivalent of copy + remove',
                    ),
    "resolve (this file)": cmd_data(
                    format_str='resolve "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='redo merges or set/view the merge status of files',
                    ),
    "revert (this file)": cmd_data(
                    format_str='revert "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='restore files to their checkout state',
                    ),
    "rollback": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='roll back the last transaction (dangerous)',
                    ),
    "root": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='print the root (top) of the current working directory',
                    ),
    "showconfig": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show combined config settings from all hgrc files',
                    ),
    "status": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Status Report.hidden-tmLanguage',
                    help='show changed files in the working directory',
                    ),
    "status (this file)": cmd_data(
                    format_str='status "%(file_name)s"',
                    prompt='',
                    enabled=True,
                    syntax_file='Packages/SublimeHg/Support/Mercurial Status Report.hidden-tmLanguage',
                    help='show changed files in the working directory',
                    ),
    "summary": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='summarize working directory state',
                    ),
    "tag...": cmd_data(
                    format_str='tag "%(input)s"',
                    prompt="Tag name:",
                    enabled=True,
                    syntax_file='',
                    help='add one or more tags for the current or given revision',
                    ),
    "tags": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='list repository tags',
                    ),
    "tip": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='show the tip revision',
                    ),
    "update": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='update working directory (or switch revisions)',
                    ),
    "update...": cmd_data(
                    format_str='update "%(input)s"',
                    prompt="Branch:",
                    enabled=True,
                    syntax_file='',
                    help='update working directory (or switch revisions)',
                    ),
    "verify": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='verify the integrity of the repository',
                    ),
    "version": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True,
                    syntax_file='',
                    help='output version and copyright information',
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
                        help='',
                        ),
        "qdiff": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='Packages/Diff/Diff.tmLanguage',
                        help='',
                        ),
        "qgoto...": cmd_data(
                        format_str='qgoto "%(input)s"',
                        prompt="Patch name:",
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qheader": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qheader...": cmd_data(
                        format_str='qheader "%(input)s"',
                        prompt="Patch name:",
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qnext": cmd_data(
                        format_str='qnext -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qpop": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qprev": cmd_data(
                        format_str='qprev -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qpush": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qrefresh": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qrefresh... (EDIT commit message)": cmd_data(
                        format_str='qrefresh -e',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qrefresh... (NEW commit message)": cmd_data(
                        format_str='qrefresh -m "%(input)s"',
                        prompt="Commit message:",
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qseries": cmd_data(
                        format_str='qseries -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qfinish...": cmd_data(
                        format_str='qfinish "%(input)s"',
                        prompt='Patch name:',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qnew...": cmd_data(
                        format_str='qnew "%(input)s"',
                        prompt='Patch name:',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qtop": cmd_data(
                        format_str='qtop -s',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
        "qunapplied": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True,
                        syntax_file='',
                        help='',
                        ),
    } 


    HG_COMMANDS.update(MQ_CMDS)

HG_COMMANDS_AND_SHORT_HELP = [[x, HG_COMMANDS[x].help] for x in HG_COMMANDS]
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
    print HG_COMMANDS_AND_SHORT_HELP
