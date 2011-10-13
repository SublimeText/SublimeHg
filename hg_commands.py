from collections import namedtuple


cmd_data = namedtuple('cmd_data','format_str prompt enabled')

HG_COMMANDS = {
    'status': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'commit': cmd_data(
                    format_str='commit -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True),
    'add': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'add (this file)': cmd_data(
                    format_str='add "%(file_name)s"',
                    prompt='',
                    enabled=True),
    'addremove': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'annotate (this file)': cmd_data(
                    format_str='annotate "%(file_name)s"',
                    prompt='',
                    enabled=True),
    'bookmark (parent revision)': cmd_data(
                    format_str='bookmark "%(input)s"',
                    prompt='Bookmark name:',
                    enabled=True),
    'bookmarks': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'branch': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'branches': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'commit (this file)': cmd_data(
                    format_str='commit "%(file_name)s" -m "%(input)s"',
                    prompt='Commit message:',
                    enabled=True),
    'diff': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'diff (this file)': cmd_data(
                    format_str='diff "%(file_name)s"',
                    prompt='',
                    enabled=True),
    'forget (this file)': cmd_data(
                    format_str='forget "%(file_name)s"',
                    prompt='',
                    enabled=True),
    'grep...': cmd_data(
                    format_str='grep "%(input)s"',
                    prompt='Pattern (grep):',
                    enabled=True),
    'heads': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'help': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'help...': cmd_data(
                    format_str='help "%(input)s"',
                    prompt='Help topic:',
                    enabled=True),
    'indentify': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'incoming': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'locate...': cmd_data(
                    format_str='locate "%(input)s"',
                    prompt='Pattern:',
                    enabled=True),
    'log': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'log (this file)': cmd_data(
                    format_str='log "%(file_name)s"',
                    prompt='',
                    enabled=True),
    'manifest': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'merge': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'merge...': cmd_data(
                    format_str='merge "%(input)s"',
                    prompt='',
                    enabled=True),
    'outgoing': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'parents': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'pull': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    'push': cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "push...": cmd_data(
                    format_str='push "%(input)s"',
                    prompt="Push target:",
                    enabled=True),
    "recover": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "remove (this file)...": cmd_data(
                    format_str='remove "%(input)s"',
                    prompt='',
                    enabled=True),
    "rename (this file)...": cmd_data(
                    format_str='rename "%(file_name)s" "%(input)s"',
                    prompt="New name:",
                    enabled=True),
    "resolve (this file)": cmd_data(
                    format_str='resolve "%(file_name)s"',
                    prompt='',
                    enabled=True),
    "revert (this file)": cmd_data(
                    format_str='revert "%(file_name)s"',
                    prompt='',
                    enabled=True),
    "rollback": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "root": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "showconfig": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "status": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "status (this file)": cmd_data(
                    format_str='status "%(file_name)s"',
                    prompt='',
                    enabled=True),
    "summary": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "tag...": cmd_data(
                    format_str='tag "%(input)s"',
                    prompt="Tag name:",
                    enabled=True),
    "tags": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "tip": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "update": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "update...": cmd_data(
                    format_str='update "%(input)s"',
                    prompt="Branch:",
                    enabled=True),
    "verify": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
    "version": cmd_data(
                    format_str='',
                    prompt='',
                    enabled=True),
}

# At some point we'll let the user choose whether to load extensions.
if True:
    MQ_CMDS = {
        "qapplied": cmd_data(
                        format_str='qapplied -s',
                        prompt='',
                        enabled=True),
        "qdiff": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
        "qgoto...": cmd_data(
                        format_str='qgoto "%(input)s"',
                        prompt="Patch name:",
                        enabled=True),
        "qheader": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
        "qheader...": cmd_data(
                        format_str='qheader "%(input)s"',
                        prompt="Patch name:",
                        enabled=True),
        "qnext": cmd_data(
                        format_str='qnext -s',
                        prompt='',
                        enabled=True),
        "qpop": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
        "qprev": cmd_data(
                        format_str='qprev -s',
                        prompt='',
                        enabled=True),
        "qpush": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
        "qrefresh": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
        "qrefresh... (EDIT commit message)": cmd_data(
                        format_str='qrefresh -e',
                        prompt='',
                        enabled=True),
        "qrefresh... (NEW commit message)": cmd_data(
                        format_str='qrefresh -m "%(input)s"',
                        prompt="Commit message:",
                        enabled=True),
        "qseries": cmd_data(
                        format_str='qseries -s',
                        prompt='',
                        enabled=True),
        "qfinish...": cmd_data(
                        format_str='qfinish "%(input)s"',
                        prompt='Patch name:',
                        enabled=True),
        "qnew...": cmd_data(
                        format_str='qnew "%(input)s"',
                        prompt='Patch name:',
                        enabled=True),
        "qtop": cmd_data(
                        format_str='qtop -s',
                        prompt='',
                        enabled=True),
        "qunapplied": cmd_data(
                        format_str='',
                        prompt='',
                        enabled=True),
    } 


    HG_COMMANDS.update(MQ_CMDS)

if __name__ == '__main__':
    print HG_COMMANDS
