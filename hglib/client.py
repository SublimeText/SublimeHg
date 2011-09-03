import subprocess, os, struct, cStringIO, collections, re
import hglib, error, util, templates, merge

from util import cmdbuilder

class hgclient(object):
    inputfmt = '>I'
    outputfmt = '>cI'
    outputfmtsize = struct.calcsize(outputfmt)
    retfmt = '>i'

    revision = collections.namedtuple('revision', 'rev, node, tags, '
                                                  'branch, author, desc')

    def __init__(self, path, encoding, configs):
        args = [hglib.HGPATH, 'serve', '--cmdserver', 'pipe',
                '--config', 'ui.interactive=True']
        if path:
            args += ['-R', path]
        if configs:
            args += ['--config'] + configs
        env = dict(os.environ)
        if encoding:
            env['HGENCODING'] = encoding

        startupinfo = None
        if os.name == 'nt':
            # Hide the child process window on Windows.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.server = subprocess.Popen(args, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, env=env,
                                       close_fds=util.closefds,
                                       startupinfo=startupinfo)

        self._readhello()
        self._version = None

    def _readhello(self):
        """ read the hello message the server sends when started """
        ch, msg = self._readchannel()
        assert ch == 'o'

        msg = msg.split('\n')

        self.capabilities = msg[0][len('capabilities: '):]
        if not self.capabilities:
            raise error.ResponseError("bad hello message: expected 'capabilities: '"
                                      ", got %r" % msg[0])

        self.capabilities = set(self.capabilities.split())

        # at the very least the server should be able to run commands
        assert 'runcommand' in self.capabilities

        self._encoding = msg[1][len('encoding: '):]
        if not self._encoding:
            raise error.ResponseError("bad hello message: expected 'encoding: '"
                                      ", got %r" % msg[1])

    def _readchannel(self):
        data = self.server.stdout.read(hgclient.outputfmtsize)
        if not data:
            raise error.ServerError()
        channel, length = struct.unpack(hgclient.outputfmt, data)
        if channel in 'IL':
            return channel, length
        else:
            return channel, self.server.stdout.read(length)

    def _parserevs(self, splitted):
        ''' splitted is a list of fields according to our rev.style, where each 6
        fields compose one revision. '''
        return [self.revision._make(rev) for rev in util.grouper(6, splitted)]

    def runcommand(self, args, inchannels, outchannels):
        def writeblock(data):
            self.server.stdin.write(struct.pack(self.inputfmt, len(data)))
            self.server.stdin.write(data)
            self.server.stdin.flush()

        if not self.server:
            raise ValueError("server not connected")

        self.server.stdin.write('runcommand\n')
        writeblock('\0'.join(args))

        while True:
            channel, data = self._readchannel()

            # input channels
            if channel in inchannels:
                writeblock(inchannels[channel](data))
            # output channels
            elif channel in outchannels:
                outchannels[channel](data)
            # result channel, command finished
            elif channel == 'r':
                return struct.unpack(hgclient.retfmt, data)[0]
            # a channel that we don't know and can't ignore
            elif channel.isupper():
                raise error.ResponseError("unexpected data on required channel '%s'"
                                          % channel)
            # optional channel
            else:
                pass

    def rawcommand(self, args, eh=None, prompt=None, input=None):
        """
        args is the cmdline (usually built using util.cmdbuilder)

        eh is an error handler that is passed the return code, stdout and stderr
        If no eh is given, we raise a CommandError if ret != 0

        prompt is used to reply to prompts by the server
        It receives the max number of bytes to return and the contents of stdout
        received so far

        input is used to reply to bulk data requests by the server
        It receives the max number of bytes to return
        """

        out, err = cStringIO.StringIO(), cStringIO.StringIO()
        outchannels = {'o' : out.write, 'e' : err.write}

        inchannels = {}
        if prompt is not None:
            def func(size):
                reply = prompt(size, out.getvalue())
                return str(reply)
            inchannels['L'] = func
        if input is not None:
            inchannels['I'] = input

        ret = self.runcommand(args, inchannels, outchannels)
        out, err = out.getvalue(), err.getvalue()

        if ret:
            if eh is None:
                raise error.CommandError(args, ret, out, err)
            else:
                return eh(ret, out, err)
        return out

    def close(self):
        """
        Closes the command server instance and waits for it to exit, returns the
        exit code.

        Attempting to call any function afterwards that needs to communicate with
        the server will raise a ValueError.
        """
        self.server.stdin.close()
        self.server.wait()
        ret = self.server.returncode
        self.server = None
        return ret

    def add(self, files=[], dryrun=False, subrepos=False, include=None,
            exclude=None):
        """
        Add the specified files on the next commit.
        If no files are given, add all files to the repository.

        dryrun - do no perform actions
        subrepos - recurse into subrepositories
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns

        Return whether all given files were added.
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('add', *files, n=dryrun, S=subrepos, I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def addremove(self, files=[], similarity=None, dryrun=False, include=None,
                  exclude=None):
        """
        Add all new files and remove all missing files from the repository.

        New files are ignored if they match any of the patterns in ".hgignore". As
        with add, these changes take effect at the next commit.

        similarity - used to detect renamed files. With a parameter
        greater than 0, this compares every removed file with every added file and
        records those similar enough as renames. This option takes a percentage
        between 0 (disabled) and 100 (files must be identical) as its parameter.
        Detecting renamed files this way can be expensive. After using this
        option, "hg status -C" can be used to check which files were identified as
        moved or renamed.

        dryrun - do no perform actions
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns

        Return True if all files are successfully added.
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('addremove', *files, s=similarity, n=dryrun, I=include,
                          X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def annotate(self, files, rev=None, nofollow=False, text=False, user=False,
                 file=False, date=False, number=False, changeset=False,
                 line=False, verbose=False, include=None, exclude=None):
        """
        Show changeset information by line for each file in files.

        rev - annotate the specified revision
        nofollow - don't follow copies and renames
        text - treat all files as text
        user - list the author (long with -v)
        file - list the filename
        date - list the date
        number - list the revision number (default)
        changeset - list the changeset
        line - show line number at the first appearance
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns

        Yields a (info, contents) tuple for each line in a file. Info is a space
        separated string according to the given options.
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('annotate', *files, r=rev, no_follow=nofollow, a=text,
                          u=user, f=file, d=date, n=number, c=changeset, l=line,
                          v=verbose, I=include, X=exclude)

        out = self.rawcommand(args)

        for line in out.splitlines():
            yield tuple(line.split(': ', 1))

    def archive(self, dest, rev=None, nodecode=False, prefix=None, type=None,
                subrepos=False, include=None, exclude=None):
        """
        Create an unversioned archive of a repository revision.

        The exact name of the destination archive or directory is given using a
        format string; see export for details.

        Each member added to an archive file has a directory prefix prepended. Use
        prefix to specify a format string for the prefix. The default is the
        basename of the archive, with suffixes removed.

        dest - destination path
        rev - revision to distribute. The revision used is the parent of the
        working directory if one isn't given.

        nodecode - do not pass files through decoders
        prefix - directory prefix for files in archive
        type - type of distribution to create. The archive type is automatically
        detected based on file extension if one isn't given.

        Valid types are:

        "files"  a directory full of files (default)
        "tar"    tar archive, uncompressed
        "tbz2"   tar archive, compressed using bzip2
        "tgz"    tar archive, compressed using gzip
        "uzip"   zip archive, uncompressed
        "zip"    zip archive, compressed using deflate

        subrepos - recurse into subrepositories
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        args = cmdbuilder('archive', dest, r=rev, no_decode=nodecode, p=prefix,
                          t=type, S=subrepos, I=include, X=exclude)

        self.rawcommand(args)

    def backout(self, rev, merge=False, parent=None, tool=None, message=None,
                logfile=None, date=None, user=None):
        """
        Prepare a new changeset with the effect of rev undone in the current
        working directory.

        If rev is the parent of the working directory, then this new changeset is
        committed automatically. Otherwise, hg needs to merge the changes and the
        merged result is left uncommitted.

        rev - revision to backout
        merge - merge with old dirstate parent after backout
        parent - parent to choose when backing out merge
        tool - specify merge tool
        message - use text as commit message
        logfile - read commit message from file
        date - record the specified date as commit date
        user - record the specified user as committer
        """
        if message and logfile:
            raise ValueError("cannot specify both a message and a logfile")

        args = cmdbuilder('backout', r=rev, merge=merge, parent=parent, t=tool,
                          m=message, l=logfile, d=date, u=user)

        self.rawcommand(args)

    def bookmark(self, name, rev=None, force=False, delete=False, inactive=False,
                 rename=None):
        """
        Set a bookmark on the working directory's parent revision or rev,
        with the given name.

        name - bookmark name
        rev - revision to bookmark
        force - bookmark even if another bookmark with the same name exists
        delete - delete the given bookmark
        inactive - do not mark the new bookmark active
        rename - rename the bookmark given by rename to name
        """
        args = cmdbuilder('bookmark', name, r=rev, f=force, d=delete,
                          i=inactive, m=rename)

        self.rawcommand(args)

    def bookmarks(self):
        """
        Return the bookmarks as a list of (name, rev, node) and the index of the
        current one.

        If there isn't a current one, -1 is returned as the index.
        """
        out = self.rawcommand(['bookmarks'])

        bms = []
        current = -1
        if out.rstrip() != 'no bookmarks set':
            for line in out.splitlines():
                iscurrent, line = line[0:3], line[3:]
                if '*' in iscurrent:
                    current = len(bms)
                name, line = line.split(' ', 1)
                rev, node = line.split(':')
                bms.append((name, int(rev), node))
        return bms, current

    def branch(self, name=None, clean=False, force=False):
        """
        When name isn't given, return the current branch name. Otherwise set the
        working directory branch name (the branch will not exist in the repository
        until the next commit). Standard practice recommends that primary
        development take place on the 'default' branch.

        When clean is True, reset and return the working directory branch to that
        of the parent of the working directory, negating a previous branch change.

        name - new branch name
        clean - reset branch name to parent branch name
        force - set branch name even if it shadows an existing branch
        """
        if name and clean:
            raise ValueError('cannot use both name and clean')

        args = cmdbuilder('branch', name, f=force, C=clean)
        out = self.rawcommand(args).rstrip()

        if name:
            return name
        elif not clean:
            return out
        else:
            # len('reset working directory to branch ') == 34
            return out[34:]

    def branches(self, active=False, closed=False):
        """
        Returns the repository's named branches as a list of (name, rev, node).

        active - show only branches that have unmerged heads
        closed - show normal and closed branches
        """
        args = cmdbuilder('branches', a=active, c=closed)
        out = self.rawcommand(args)

        branches = []
        for line in out.rstrip().splitlines():
            name, line = line.split(' ', 1)
            rev, node = line.split(':')
            node = node.split()[0] # get rid of ' (inactive)'
            branches.append((name, int(rev), node))
        return branches

    def bundle(self, file, destrepo=None, rev=[], branch=[], base=[], all=False,
               force=False, type=None, ssh=None, remotecmd=None, insecure=False):
        """
        Generate a compressed changegroup file collecting changesets not known to
        be in another repository.

        If destrepo isn't given, then hg assumes the destination will have all
        the nodes you specify with base. To create a bundle containing all
        changesets, use all (or set base to 'null').

        file - destination file name
        destrepo - repository to look for changes
        rev - a changeset intended to be added to the destination
        branch - a specific branch you would like to bundle
        base - a base changeset assumed to be available at the destination
        all - bundle all changesets in the repository
        type - bundle compression type to use, available compression methods are:
        none, bzip2, and gzip (default: bzip2)

        force - run even when the destrepo is unrelated
        ssh - specify ssh command to use
        remotecmd - specify hg command to run on the remote side
        insecure - do not verify server certificate (ignoring web.cacerts config)

        Return True if a bundle was created, False if no changes were found.
        """
        args = cmdbuilder('bundle', file, destrepo, f=force, r=rev, b=branch,
                          base=base, a=all, t=type, e=ssh, remotecmd=remotecmd,
                          insecure=insecure)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def cat(self, files, rev=None, output=None):
        """
        Return a string containing the specified files as they were at the
        given revision. If no revision is given, the parent of the working
        directory is used, or tip if no revision is checked out.

        If output is given, writes the contents to the specified file.
        The name of the file is given using a format string. The formatting rules
        are the same as for the export command, with the following additions:

        "%s"  basename of file being printed
        "%d"  dirname of file being printed, or '.' if in repository root
        "%p"  root-relative path name of file being printed
        """
        args = cmdbuilder('cat', *files, r=rev, o=output)
        out = self.rawcommand(args)

        if not output:
            return out

    def clone(self, source='.', dest=None, branch=None, updaterev=None,
              revrange=None):
        """
        Create a copy of an existing repository specified by source in a new
        directory dest.

        If dest isn't specified, it defaults to the basename of source.

        branch - clone only the specified branch
        updaterev - revision, tag or branch to check out
        revrange - include the specified changeset
        """
        args = cmdbuilder('clone', source, dest, b=branch, u=updaterev, r=revrange)
        self.rawcommand(args)

    def commit(self, message=None, logfile=None, addremove=False, closebranch=False,
               date=None, user=None, include=None, exclude=None):
        """
        Commit changes reported by status into the repository.

        message - the commit message
        logfile - read commit message from file
        addremove - mark new/missing files as added/removed before committing
        closebranch - mark a branch as closed, hiding it from the branch list
        date - record the specified date as commit date
        user - record the specified user as committer
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if message is None and logfile is None:
            raise ValueError("must provide at least a message or a logfile")
        elif message and logfile:
            raise ValueError("cannot specify both a message and a logfile")

        # --debug will print the committed cset
        args = cmdbuilder('commit', debug=True, m=message, A=addremove,
                          close_branch=closebranch, d=date, u=user, l=logfile,
                          I=include, X=exclude)

        out = self.rawcommand(args)
        rev, node = out.splitlines()[-1].rsplit(':')
        return int(rev.split()[-1]), node

    def config(self, names=[], untrusted=False, showsource=False):
        """
        Return a list of (section, key, value) config settings from all hgrc files

        When showsource is specified, return (source, section, key, value) where
        source is of the form filename:[line]
        """
        def splitline(s):
            k, value = s.rstrip().split('=', 1)
            section, key = k.split('.', 1)
            return (section, key, value)

        if not isinstance(names, list):
            names = [names]

        args = cmdbuilder('showconfig', *names, u=untrusted, debug=showsource)
        out = self.rawcommand(args)

        conf = []
        if showsource:
            out = util.skiplines(out, 'read config from: ')
            for line in out.splitlines():
                m = re.match(r"(.+?:(?:\d+:)?) (.*)", line)
                t = splitline(m.group(2))
                conf.append((m.group(1)[:-1], t[0], t[1], t[2]))
        else:
            for line in out.splitlines():
                conf.append(splitline(line))

        return conf

    @property
    def encoding(self):
        """
        Return the server's encoding (as reported in the hello message).
        """
        if not 'getencoding' in self.capabilities:
            raise CapabilityError('getencoding')

        if not self._encoding:
            self.server.stdin.write('getencoding\n')
            self._encoding = self._readfromchannel('r')

        return self._encoding

    def copy(self, source, dest, after=False, force=False, dryrun=False,
             include=None, exclude=None):
        """
        Mark dest as having copies of source files. If dest is a directory, copies
        are put in that directory. If dest is a file, then source must be a string.

        Returns True on success, False if errors are encountered.

        source - a file or a list of files
        dest - a destination file or directory
        after - record a copy that has already occurred
        force - forcibly copy over an existing managed file
        dryrun - do not perform actions, just print output
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(source, list):
            source = [source]

        source.append(dest)
        args = cmdbuilder('copy', *source, A=after, f=force, n=dryrun,
                          I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def diff(self, files=[], revs=[], change=None, text=False,
             git=False, nodates=False, showfunction=False, reverse=False,
             ignoreallspace=False, ignorespacechange=False, ignoreblanklines=False,
             unified=None, stat=False, subrepos=False, include=None, exclude=None):
        """
        Return differences between revisions for the specified files.

        revs - a revision or a list of two revisions to diff
        change - change made by revision
        text - treat all files as text
        git - use git extended diff format
        nodates - omit dates from diff headers
        showfunction - show which function each change is in
        reverse - produce a diff that undoes the changes
        ignoreallspace - ignore white space when comparing lines
        ignorespacechange - ignore changes in the amount of white space
        ignoreblanklines - ignore changes whose lines are all blank
        unified - number of lines of context to show
        stat - output diffstat-style summary of changes
        subrepos - recurse into subrepositories
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if change and revs:
            raise ValueError('cannot specify both change and rev')

        args = cmdbuilder('diff', *files, r=revs, c=change,
                          a=text, g=git, nodates=nodates,
                          p=showfunction, reverse=reverse,
                          w=ignoreallspace, b=ignorespacechange,
                          B=ignoreblanklines, U=unified, stat=stat,
                          S=subrepos, I=include, X=exclude)

        return self.rawcommand(args)

    def export(self, revs, output=None, switchparent=False, text=False, git=False,
               nodates=False):
        """
        Return the header and diffs for one or more changesets. When output is
        given, dumps to file. The name of the file is given using a format string.
        The formatting rules are as follows:

        "%%"  literal "%" character
        "%H"  changeset hash (40 hexadecimal digits)
        "%N"  number of patches being generated
        "%R"  changeset revision number
        "%b"  basename of the exporting repository
        "%h"  short-form changeset hash (12 hexadecimal digits)
        "%n"  zero-padded sequence number, starting at 1
        "%r"  zero-padded changeset revision number

        output - print output to file with formatted name
        switchparent - diff against the second parent
        rev - a revision or list of revisions to export
        text - treat all files as text
        git - use git extended diff format
        nodates - omit dates from diff headers
        """
        if not isinstance(revs, list):
            revs = [revs]
        args = cmdbuilder('export', *revs, o=output, switch_parent=switchparent,
                          a=text, g=git, nodates=nodates)

        out = self.rawcommand(args)

        if output is None:
            return out

    def forget(self, files, include=None, exclude=None):
        """
        Mark the specified files so they will no longer be tracked after the next
        commit.

        This only removes files from the current branch, not from the entire
        project history, and it does not delete them from the working directory.

        Returns True on success.

        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('forget', *files, I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def grep(self, pattern, files=[], all=False, text=False, follow=False,
             ignorecase=False, fileswithmatches=False, line=False, user=False,
             date=False, include=None, exclude=None):
        """
        Search for a pattern in specified files and revisions.

        This behaves differently than Unix grep. It only accepts Python/Perl
        regexps. It searches repository history, not the working directory.
        It always prints the revision number in which a match appears.

        Yields (filename, revision, [line, [match status, [user, [date, [match]]]]])
        per match depending on the given options.

        all - print all revisions that match
        text - treat all files as text
        follow - follow changeset history, or file history across copies and renames
        ignorecase - ignore case when matching
        fileswithmatches - return only filenames and revisions that match
        line - return line numbers in the result tuple
        user - return the author in the result tuple
        date - return the date in the result tuple
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('grep', *[pattern] + files, all=all, a=text, f=follow,
                          i=ignorecase, l=fileswithmatches, n=line, u=user, d=date,
                          I=include, X=exclude)
        args.append('-0')

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)
            return ''

        out = self.rawcommand(args, eh=eh).split('\0')

        fieldcount = 3
        if user:
            fieldcount += 1
        if date:
            fieldcount += 1
        if line:
            fieldcount += 1
        if all:
            fieldcount += 1
        if fileswithmatches:
            fieldcount -= 1

        return util.grouper(fieldcount, out)

    def heads(self, rev=[], startrev=[], topological=False, closed=False):
        """
        Return a list of current repository heads or branch heads.

        rev - return only branch heads on the branches associated with the specified
        changesets.

        startrev - return only heads which are descendants of the given revs.
        topological - named branch mechanics will be ignored and only changesets
        without children will be shown.

        closed - normal and closed branch heads.
        """
        if not isinstance(rev, list):
            rev = [rev]

        args = cmdbuilder('heads', *rev, r=startrev, t=topological, c=closed,
                          template=templates.changeset)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)
            return ''

        out = self.rawcommand(args, eh=eh).split('\0')[:-1]
        return self._parserevs(out)

    def identify(self, rev=None, source=None, num=False, id=False, branch=False,
                 tags=False, bookmarks=False):
        """
        Return a summary string identifying the repository state at rev using one or
        two parent hash identifiers, followed by a "+" if the working directory has
        uncommitted changes, the branch name (if not default), a list of tags, and
        a list of bookmarks.

        When rev is not given, return a summary string of the current state of the
        repository.

        Specifying source as a repository root or Mercurial bundle will cause
        lookup to operate on that repository/bundle.

        num - show local revision number
        id - show global revision id
        branch - show branch
        tags - show tags
        bookmarks - show bookmarks
        """
        args = cmdbuilder('identify', source, r=rev, n=num, i=id, b=branch, t=tags,
                          B=bookmarks)

        return self.rawcommand(args)

    def import_(self, patches, strip=None, force=False, nocommit=False,
                bypass=False, exact=False, importbranch=False, message=None,
                date=None, user=None, similarity=None):
        """
        Import the specified patches which can be a list of file names or a
        file-like object and commit them individually (unless nocommit is
        specified).

        strip - directory strip option for patch. This has the same meaning as the
        corresponding patch option (default: 1)

        force - skip check for outstanding uncommitted changes
        nocommit - don't commit, just update the working directory
        bypass - apply patch without touching the working directory
        exact - apply patch to the nodes from which it was generated
        importbranch - use any branch information in patch (implied by exact)
        message - the commit message
        date - record the specified date as commit date
        user - record the specified user as committer
        similarity - guess renamed files by similarity (0<=s<=100)
        """
        if hasattr(patches, 'read') and hasattr(patches, 'readline'):
            patch = patches

            def readline(size, output):
                return patch.readline(size)

            stdin = True
            patches = ()
            prompt = readline
            input = patch.read
        else:
            stdin = False
            prompt = None
            input = None

        args = cmdbuilder('import', *patches, strip=strip, force=force,
                          nocommit=nocommit, bypass=bypass, exact=exact,
                          importbranch=importbranch, message=message,
                          date=date, user=user, similarity=similarity, _=stdin)

        self.rawcommand(args, prompt=prompt, input=input)

    def incoming(self, revrange=None, path=None, force=False, newest=False,
                 bundle=None, bookmarks=False, branch=None, limit=None,
                 nomerges=False, subrepos=False):
        """
        Return new changesets found in the specified path or the default pull
        location.

        When bookmarks=True, return a list of (name, node) of incoming bookmarks.

        revrange - a remote changeset or list of changesets intended to be added
        force - run even if remote repository is unrelated
        newest - show newest record first
        bundle - avoid downloading the changesets twice and store the bundles into
        the specified file.

        bookmarks - compare bookmarks (this changes the return value)
        branch - a specific branch you would like to pull
        limit - limit number of changes returned
        nomerges - do not show merges
        ssh - specify ssh command to use
        remotecmd - specify hg command to run on the remote side
        insecure- do not verify server certificate (ignoring web.cacerts config)
        subrepos - recurse into subrepositories
        """
        args = cmdbuilder('incoming',
                          path,
                          template=templates.changeset, r=revrange,
                          f=force, n=newest, bundle=bundle,
                          B=bookmarks, b=branch, l=limit, M=nomerges, S=subrepos)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2)
        if bookmarks:
            bms = []
            for line in out.splitlines():
                bms.append(tuple(line.split()))
            return bms
        else:
            out = out.split('\0')[:-1]
            return self._parserevs(out)

    def log(self, revrange=None, files=[], follow=False, followfirst=False,
            date=None, copies=False, keyword=None, removed=False, onlymerges=False,
            user=None, branch=None, prune=None, hidden=False, limit=None,
            nomerges=False, include=None, exclude=None):
        """
        Return the revision history of the specified files or the entire project.

        File history is shown without following rename or copy history of files.
        Use follow with a filename to follow history across renames and copies.
        follow without a filename will only show ancestors or descendants of the
        starting revision. followfirst only follows the first parent of merge
        revisions.

        If revrange isn't specified, the default is "tip:0" unless follow is set,
        in which case the working directory parent is used as the starting
        revision.

        The returned changeset is a named tuple with the following string fields:
            - rev
            - node
            - tags (space delimited)
            - branch
            - author
            - desc

        follow - follow changeset history, or file history across copies and renames
        followfirst - only follow the first parent of merge changesets
        date - show revisions matching date spec
        copies - show copied files
        keyword - do case-insensitive search for a given text
        removed - include revisions where files were removed
        onlymerges - show only merges
        user - revisions committed by user
        branch - show changesets within the given named branch
        prune - do not display revision or any of its ancestors
        hidden - show hidden changesets
        limit - limit number of changes displayed
        nomerges - do not show merges
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        args = cmdbuilder('log', *files, template=templates.changeset,
                          r=revrange, f=follow, follow_first=followfirst,
                          d=date, C=copies, k=keyword, removed=removed,
                          m=onlymerges, u=user, b=branch, P=prune, h=hidden,
                          l=limit, M=nomerges, I=include, X=exclude)

        out = self.rawcommand(args)
        out = out.split('\0')[:-1]

        return self._parserevs(out)

    def manifest(self, rev=None, all=False):
        """
        Yields (nodeid, permission, executable, symlink, file path) tuples for
        version controlled files for the given revision. If no revision is given,
        the first parent of the working directory is used, or the null revision if
        no revision is checked out.

        When all is True, all files from all revisions are yielded (just the name).
        This includes deleted and renamed files.
        """
        args = cmdbuilder('manifest', r=rev, all=all, debug=True)

        out = self.rawcommand(args)

        if all:
            for line in out.splitlines():
                yield line
        else:
            for line in out.splitlines():
                node = line[0:40]
                perm = line[41:44]
                symlink = line[45] == '@'
                executable = line[45] == '*'
                yield (node, perm, executable, symlink, line[47:])

    def merge(self, rev=None, force=False, tool=None, cb=merge.handlers.abort):
        """
        Merge working directory with rev. If no revision is specified, the working
        directory's parent is a head revision, and the current branch contains
        exactly one other head, the other head is merged with by default.

        The current working directory is updated with all changes made in the
        requested revision since the last common predecessor revision.

        Files that changed between either parent are marked as changed for the
        next commit and a commit must be performed before any further updates to
        the repository are allowed. The next commit will have two parents.

        force - force a merge with outstanding changes
        tool - can be used to specify the merge tool used for file merges. It
        overrides the HGMERGE environment variable and your configuration files.

        cb - controls the behaviour when Mercurial prompts what to do with regard
        to a specific file, e.g. when one parent modified a file and the other
        removed it. It can be one of merge.handlers, or a function that gets a
        single argument which are the contents of stdout. It should return one
        of the expected choices (a single character).
        """
        # we can't really use --preview since merge doesn't support --template
        args = cmdbuilder('merge', r=rev, f=force, t=tool)

        prompt = None
        if cb is merge.handlers.abort:
            prompt = cb
        elif cb is merge.handlers.noninteractive:
            args.append('-y')
        else:
            prompt = lambda size, output: cb(output) + '\n'

        self.rawcommand(args, prompt=prompt)

    def move(self, source, dest, after=False, force=False, dryrun=False,
             include=None, exclude=None):
        """
        Mark dest as copies of source; mark source for deletion. If dest is a
        directory, copies are put in that directory. If dest is a file, then source
        must be a string.

        Returns True on success, False if errors are encountered.

        source - a file or a list of files
        dest - a destination file or directory
        after - record a rename that has already occurred
        force - forcibly copy over an existing managed file
        dryrun - do not perform actions, just print output
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(source, list):
            source = [source]

        source.append(dest)
        args = cmdbuilder('move', *source, A=after, f=force, n=dryrun,
                          I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def outgoing(self, revrange=None, path=None, force=False, newest=False,
                 bookmarks=False, branch=None, limit=None, nomerges=False,
                 subrepos=False):
        """
        Return changesets not found in the specified path or the default push
        location.

        When bookmarks=True, return a list of (name, node) of bookmarks that will
        be pushed.

        revrange - a (list of) changeset intended to be included in the destination
        force - run even when the destination is unrelated
        newest - show newest record first
        branch - a specific branch you would like to push
        limit - limit number of changes displayed
        nomerges - do not show merges
        ssh - specify ssh command to use
        remotecmd - specify hg command to run on the remote side
        insecure - do not verify server certificate (ignoring web.cacerts config)
        subrepos - recurse into subrepositories
        """
        args = cmdbuilder('outgoing',
                          path,
                          template=templates.changeset, r=revrange,
                          f=force, n=newest, B=bookmarks,
                          b=branch, S=subrepos)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2)
        if bookmarks:
            bms = []
            for line in out.splitlines():
                bms.append(tuple(line.split()))
            return bms
        else:
            out = out.split('\0')[:-1]
            return self._parserevs(out)

    def parents(self, rev=None, file=None):
        """
        Return the working directory's parent revisions. If rev is given, the
        parent of that revision will be printed. If file is given, the revision
        in which the file was last changed (before the working directory revision
        or the revision specified by rev) is returned.
        """
        args = cmdbuilder('parents', file, template=templates.changeset, r=rev)

        out = self.rawcommand(args)
        if not out:
            return

        out = out.split('\0')[:-1]

        return self._parserevs(out)

    def paths(self, name=None):
        """
        Return the definition of given symbolic path name. If no name is given,
        return a dictionary of pathname : url of all available names.

        Path names are defined in the [paths] section of your configuration file
        and in "/etc/mercurial/hgrc". If run inside a repository, ".hg/hgrc" is
        used, too.
        """
        if not name:
            out = self.rawcommand(['paths'])
            if not out:
                return {}

            return dict([s.split(' = ') for s in out.rstrip().split('\n')])
        else:
            args = cmdbuilder('paths', name)
            out = self.rawcommand(args)
            return out.rstrip()

    def pull(self, source=None, rev=None, update=False, force=False, bookmark=None,
             branch=None, ssh=None, remotecmd=None, insecure=False, tool=None):
        """
        Pull changes from a remote repository.

        This finds all changes from the repository specified by source and adds
        them to this repository. If source is omitted, the 'default' path will be
        used. By default, this does not update the copy of the project in the
        working directory.

        Returns True on success, False if update was given and there were
        unresolved files.

        update - update to new branch head if changesets were pulled
        force - run even when remote repository is unrelated
        rev - a (list of) remote changeset intended to be added
        bookmark - (list of) bookmark to pull
        branch - a (list of) specific branch you would like to pull
        ssh - specify ssh command to use
        remotecmd - specify hg command to run on the remote side
        insecure - do not verify server certificate (ignoring web.cacerts config)
        tool - specify merge tool for rebase
        """
        args = cmdbuilder('pull', source, r=rev, u=update, f=force, B=bookmark,
                          b=branch, e=ssh, remotecmd=remotecmd, insecure=insecure,
                          t=tool)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def push(self, dest=None, rev=None, force=False, bookmark=None, branch=None,
             newbranch=False, ssh=None, remotecmd=None, insecure=False):
        """
        Push changesets from this repository to the specified destination.

        This operation is symmetrical to pull: it is identical to a pull in the
        destination repository from the current one.

        Returns True if push was successful, False if nothing to push.

        rev - the (list of) specified revision and all its ancestors will be pushed
        to the remote repository.

        force - override the default behavior and push all changesets on all
        branches.

        bookmark - (list of) bookmark to push
        branch - a (list of) specific branch you would like to push
        newbranch - allows push to create a new named branch that is not present at
        the destination. This allows you to only create a new branch without
        forcing other changes.

        ssh - specify ssh command to use
        remotecmd - specify hg command to run on the remote side
        insecure - do not verify server certificate (ignoring web.cacerts config)
        """
        args = cmdbuilder('push', dest, r=rev, f=force, B=bookmark, b=branch,
                          new_branch=newbranch, e=ssh, remotecmd=remotecmd,
                          insecure=insecure)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def remove(self, files, after=False, force=False, include=None, exclude=None):
        """
        Schedule the indicated files for removal from the repository. This only
        removes files from the current branch, not from the entire project history.

        Returns True on success, False if any warnings encountered.

        after - used to remove only files that have already been deleted
        force - remove (and delete) file even if added or modified
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('remove', *files, A=after, f=force, I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def resolve(self, file=[], all=False, listfiles=False, mark=False, unmark=False,
                tool=None, include=None, exclude=None):
        """
        Redo merges or set/view the merge status of given files.

        Returns True on success, False if any files fail a resolve attempt.

        When listfiles is True, returns a list of (code, file path) of resolved
        and unresolved files. Code will be 'R' or 'U' accordingly.

        all - select all unresolved files
        mark - mark files as resolved
        unmark - mark files as unresolved
        tool - specify merge tool
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if not isinstance(file, list):
            file = [file]

        args = cmdbuilder('resolve', *file, a=all, l=listfiles, m=mark, u=unmark,
                          t=tool, I=include, X=exclude)

        out = self.rawcommand(args)

        if listfiles:
            l = []
            for line in out.splitlines():
                l.append(tuple(line.split(' ', 1)))
            return l

    def revert(self, files, rev=None, all=False, date=None, nobackup=False,
               dryrun=False, include=None, exclude=None):
        """
        With no revision specified, revert the specified files or directories to
        the contents they had in the parent of the working directory. This
        restores the contents of files to an unmodified state and unschedules
        adds, removes, copies, and renames. If the working directory has two
        parents, you must explicitly specify a revision.

        Specifying rev or date will revert the given files or directories to their
        states as of a specific revision. Because revert does not change the
        working directory parents, this will cause these files to appear modified.
        This can be helpful to "back out" some or all of an earlier change.

        Modified files are saved with a .orig suffix before reverting. To disable
        these backups, use nobackup.

        Returns True on success.

        all - revert all changes when no arguments given
        date - tipmost revision matching date
        rev - revert to the specified revision
        nobackup - do not save backup copies of files
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        dryrun - do not perform actions, just print output
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('revert', *files, r=rev, a=all, d=date,
                          no_backup=nobackup, n=dryrun, I=include, X=exclude)

        eh = util.reterrorhandler(args)
        self.rawcommand(args, eh=eh)

        return bool(eh)

    def root(self):
        """
        Return the root directory of the current repository.
        """
        return self.rawcommand(['root']).rstrip()

    def status(self, rev=None, change=None, all=False, modified=False, added=False,
               removed=False, deleted=False, clean=False, unknown=False,
               ignored=False, copies=False, subrepos=False, include=None,
               exclude=None):
        """
        Return status of files in the repository as a list of (code, file path)
        where code can be:

                M = modified
                A = added
                R = removed
                C = clean
                ! = missing (deleted by non-hg command, but still tracked)
                ? = untracked
                I = ignored
                  = origin of the previous file listed as A (added)

        rev - show difference from (list of) revision
        change - list the changed files of a revision
        all - show status of all files
        modified - show only modified files
        added - show only added files
        removed - show only removed files
        deleted - show only deleted (but tracked) files
        clean - show only files without changes
        unknown - show only unknown (not tracked) files
        ignored - show only ignored files
        copies - show source of copied files
        subrepos - recurse into subrepositories
        include - include names matching the given patterns
        exclude - exclude names matching the given patterns
        """
        if rev and change:
            raise ValueError('cannot specify both rev and change')

        args = cmdbuilder('status', rev=rev, change=change, A=all, m=modified,
                          a=added, r=removed, d=deleted, c=clean, u=unknown,
                          i=ignored, C=copies, S=subrepos, I=include, X=exclude)

        args.append('-0')

        out = self.rawcommand(args)
        l = []

        for entry in out.split('\0'):
            if entry:
                if entry[0] == ' ':
                    l.append((' ', entry[2:]))
                else:
                    l.append(tuple(entry.split(' ', 1)))

        return l

    def tag(self, names, rev=None, message=None, force=False, local=False,
            remove=False, date=None, user=None):
        """
        Add one or more tags specified by names for the current or given revision.

        Changing an existing tag is normally disallowed; use force to override.

        Tag commits are usually made at the head of a branch. If the parent of the
        working directory is not a branch head, a CommandError will be raised.
        force can be specified to force the tag commit to be based on a non-head
        changeset.

        local - make the tag local
        rev - revision to tag
        remove - remove a tag
        message - set commit message
        date - record the specified date as commit date
        user - record the specified user as committer
        """
        if not isinstance(names, list):
            names = [names]

        args = cmdbuilder('tag', *names, r=rev, m=message, f=force, l=local,
                          remove=remove, d=date, u=user)

        self.rawcommand(args)

    def tags(self):
        """
        Return a list of repository tags as: (name, rev, node, islocal)
        """
        args = cmdbuilder('tags', v=True)

        out = self.rawcommand(args)

        t = []
        for line in out.splitlines():
            taglocal = line.endswith(' local')
            if taglocal:
                line = line[:-6]
            name, rev = line.rsplit(' ', 1)
            rev, node = rev.split(':')
            t.append((name.rstrip(), int(rev), node, taglocal))
        return t

    def summary(self, remote=False):
        """
        Return a dictionary with a brief summary of the working directory state,
        including parents, branch, commit status, and available updates.

            'parent' : a list of (rev, node, tags, message)
            'branch' : the current branch
            'commit' : True if the working directory is clean, False otherwise
            'update' : number of available updates,
            ['remote' : (in, in bookmarks, out, out bookmarks),]
            ['mq': (applied, unapplied) mq patches,]

            unparsed entries will be of them form key : value
        """
        args = cmdbuilder('summary', remote=remote)

        out = self.rawcommand(args).splitlines()

        d = {}
        while out:
            line = out.pop(0)
            name, value = line.split(': ', 1)

            if name == 'parent':
                parent, tags = value.split(' ', 1)
                rev, node = parent.split(':')

                if tags:
                    tags = tags.replace(' (empty repository)', '')
                else:
                    tags = None

                value = d.get(name, [])

                if rev == '-1':
                    value.append((int(rev), node, tags, None))
                else:
                    message = out.pop(0)[1:]
                    value.append((int(rev), node, tags, message))
            elif name == 'branch':
                pass
            elif name == 'commit':
                value = value == '(clean)'
            elif name == 'update':
                if value == '(current)':
                    value = 0
                else:
                    value = int(value.split(' ', 1)[0])
            elif remote and name == 'remote':
                if value == '(synced)':
                    value = 0, 0, 0, 0
                else:
                    inc = incb = out_ = outb = 0

                    for v in value.split(', '):
                        count, v = v.split(' ', 1)
                        if v == 'outgoing':
                            out_ = int(count)
                        elif v.endswith('incoming'):
                            inc = int(count)
                        elif v == 'incoming bookmarks':
                            incb = int(count)
                        elif v == 'outgoing bookmarks':
                            outb = int(count)

                    value = inc, incb, out_, outb
            elif name == 'mq':
                applied = unapplied = 0
                for v in value.split(', '):
                    count, v = v.split(' ', 1)
                    if v == 'applied':
                        applied = int(count)
                    elif v == 'unapplied':
                        unapplied = int(count)
                value = applied, unapplied

            d[name] = value

        return d

    def tip(self):
        """
        Return the tip revision (usually just called the tip) which is the
        changeset most recently added to the repository (and therefore the most
        recently changed head).
        """
        args = cmdbuilder('tip', template=templates.changeset)
        out = self.rawcommand(args)
        out = out.split('\0')

        return self._parserevs(out)[0]

    def update(self, rev=None, clean=False, check=False, date=None):
        """
        Update the repository's working directory to changeset specified by rev.
        If rev isn't specified, update to the tip of the current named branch.

        Return the number of files (updated, merged, removed, unresolved)

        clean - discard uncommitted changes (no backup)
        check - update across branches if no uncommitted changes
        date - tipmost revision matching date
        """
        if clean and check:
            raise ValueError('clean and check cannot both be True')

        args = cmdbuilder('update', r=rev, C=clean, c=check, d=date)

        def eh(ret, out, err):
            if ret == 1:
                return out

            raise error.CommandError(args, ret, out, err)


        out = self.rawcommand(args, eh=eh)

        # filter out 'merging ...' lines
        out = util.skiplines(out, 'merging ')

        counters = out.rstrip().split(', ')
        return tuple(int(s.split(' ', 1)[0]) for s in counters)

    @property
    def version(self):
        """
        Return hg version that runs the command server as a 4 fielded tuple: major,
        minor, micro and local build info. e.g. (1, 9, 1, '+4-3095db9f5c2c')
        """
        if self._version is None:
            v = self.rawcommand(cmdbuilder('version', q=True))
            v = list(re.match(r'.*?(\d+)\.(\d+)\.?(\d+)?(\+[0-9a-f-]+)?',
                              v).groups())

            for i in range(3):
                try:
                    v[i] = int(v[i])
                except TypeError:
                    v[i] = 0

            self._version = tuple(v)

        return self._version
