import sublime
import sublime_plugin

import sys
import struct
import subprocess
import os
import atexit
import shlex


running_server = None


class HGServer(object):
    """I drive a Mercurial command server (Mercurial>=1.9).

    Mercurial command server protocol: http://mercurial.selenic.com/wiki/CommandServer
    """
    def __init__(self, hg_exe='hg'):
        global running_server
        if not running_server or running_server.stdin.closed:
            startupinfo = None
            if os.name == 'nt':
                # Hide the child process window on Windows.
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.server = subprocess.Popen(
                                    [hg_exe, "serve", "--cmdserver", "pipe"],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    startupinfo=startupinfo
                                    )

            # Is this needed?
            atexit.register(self.shut_down)

            self.receive_greeting()
            self.encoding = self.get_encoding()

            running_server = self.server
            return

        # Reuse existing server.
        self.server = running_server
        self.encoding = self.get_encoding()
    
    def receive_greeting(self):
        try:
            channel, data = self.read_data()
        except struct.error:
            err = self.server.stderr.read()
            raise EnvironmentError(err)
        except EnvironmentError:
            err = self.server.stderr.read()
            raise EnvironmentError(err)

        try:
            caps, enc = data.split('\n')
        except ValueError:
            # Means the server isn't returning the promised data, so the
            # environment is wrong.
            print "SublimeHg:err: SublimeHg requires Mercurial>=1.9. (Probable cause.)"
            raise EnvironmentError("SublimeHg requires Mercurial>=1.9")
            
        caps = ', '.join(caps.split()[1:])
        print "SublimeHg:inf:", "Capabilities:", caps
        print "SublimeHg:inf: Encoding:", enc.split()[1]

    def read_data(self):
        channel, length = struct.unpack('>cI', self.server.stdout.read(5))
        if channel in 'IL':
            return channel, length
        
        return channel, self.server.stdout.read(length)
    
    def write_block(self, cmd, *args):
        self.server.stdin.write(cmd + '\n')

        if args:
            data = '\0'.join(args)
            length = struct.pack('>l', len(data))
            self.server.stdin.write(length + data)
            self.server.stdin.flush()

    def write_zero(self):
        length = struct.pack('>l', 0)
        self.server.stdin.write(length)

    def run_command(self, *args):
        if len(args) == 1 and ' ' in args[0]:
            args = shlex.split(args[0])

        if args[0] == 'hg':
            print "SublimeHg:inf: Stripped superfluous 'hg' from '%s'" % ' '.join(args)
            args = args[1:]
        
        print "SublimeHg:inf: Sending command '%s' as %s" % (' '.join(args), args)
        self.write_block('runcommand', *args)

        rv = ''
        while True:
            channel, line = self.read_data()
            if channel == 'o':
                rv += line
            elif channel == 'r':
                print "SublimeHg:inf: Return value: %s" % struct.unpack('>l', line)[0]
                return rv[:-1]
            elif channel in 'IL':
                # Tell server wo won't send any input.
                self.write_zero()
            elif channel == 'e':
                print "SublimeHg:err: " + line[:-1]
                rv = line
    
    def get_encoding(self):
        self.write_block('getencoding')
        return self.read_data()[1]

    def shut_down(self):
        print "SublimeHg:inf: Shutting down HG server..."
        if not self.server.stdin.closed:
            self.server.stdin.close()


class HgCmdLineCommand(sublime_plugin.TextCommand):

    def configure(self):
        s = sublime.load_settings('Global.sublime-settings')
        user_exe = s.get('packages.sublime_hg.hg_exe')
        self.hg_exe = user_exe or 'hg'

    def run(self, edit, cmd=None):
        self.edit = edit
        if not cmd:
            self.view.window().show_input_panel('Hg command:', 'status', self.on_done, None, None)
            return
        self.on_done(cmd)
    
    def on_done(self, s):
        old_cd = os.getcwd()
        os.chdir(os.path.dirname(self.view.file_name()))

        if not hasattr(self, 'hg_exe'):
            self.configure()

        try:
            hgs = HGServer(self.hg_exe)
        except EnvironmentError, e:
            sublime.status_message("SublimeHg:err:" + str(e))
            os.chdir(old_cd)
            return

        try:
            # Where's the encoding done here?
            data = hgs.run_command(s.encode(hgs.encoding))
            p = self.view.window().get_output_panel('hgs')
            p.insert(self.edit, 0, data.decode(hgs.encoding))
            self.view.window().run_command('show_panel', {'panel': 'output.hgs'})
        except UnicodeDecodeError, e:
            print "Oops (funny characters!)..."
            print e
        finally:
            os.chdir(old_cd)


# TODO: Add serve and start in a separate process?
SUBLIMEHG_CMDS = {
    # Used named tuples
    "add": ['', None],
    "add (this file)": ['add "%(file_name)s"', None],
    "addremove": ['', None],
    "annotate (this file)": ['annotate "%(file_name)s"', None],
    # "archive", # Too complicated for this simple interface?
    # "backout", # Too complicated for this simple interface?
    # "bisect", # Too complicated for this simple interface?
    "bookmark (parent revision)...": ['bookmark "%(input)s"', 'Bookmark name:'],
    "bookmarks": ['', None],
    "branch": ['', None],
    "branches": ['', None],
    # "bundle",
    # "cat",
    # "clone",
    "commit...": ['commit -m "%(input)s"', 'Commit message:'],
    "commit (this file)...": ['commit "%(file_name)s" -m "%(input)s"', "Commit message:"],
    # "copy",
    "diff": ['', None],
    "diff (this file)": ['diff "%(file_name)s"', None],
    # "export",
    "forget (this file)": ['forget "%(file_name)s"', None],
    "grep...": ['grep "%(input)s"', 'Pattern (grep):'] ,
    "heads": ['heads', None],
    "help": ['', None],
    "help...": ['help %(input)s', 'Help topic:'],
    "identify": ['', None],
    # "import",
    "incoming": ['', None],
    # "init",
    "locate...": ['locate "%(input)s"', 'Pattern (locate):'],
    "log": ['', None],
    "log (this file)": ['log "%(file_name)s"', None],
    "manifest": ['', None],
    "merge": ['', None],
    "merge...": ['merge "%(input)s"', "Revision to merge with:"],
    "outgoing": ['', None],
    "parents": ['', None],
    "paths": ['', None],
    "pull": ['', None],
    "push": ['', None],
    "push...": ['push "%(input)s"', "Push target:"],
    "recover": ['', None],
    "remove (this file)...": ['remove "%(input)s"', None],
    "rename (this file)...": ['rename "%(file_name)s" "%(input)s"', "New name:"],
    "resolve (this file)": ['resolve "%(file_name)s"', None],
    "revert (this file)": ['revert "%(file_name)s"', None],
    "rollback": ['', None],
    "root": ['', None],
    "showconfig": ['', None],
    "status": ['', None],
    "status (this file)": ['status "%(file_name)s"', None],
    "summary": ['', None],
    "tag...": ['tag "%(input)s"', "Tag name:"],
    "tags": ['', None],
    "tip": ['', None],
    # "unbundle",
    "update": ['', None],
    "update...": ['update "%(input)s"', "Branch:"],
    "verify": ['', None],
    "version": ['', None]
    }


class HgCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.edit = edit
        self.view.window().show_quick_panel(sorted(SUBLIMEHG_CMDS.keys()),
                                                                self.on_done)
    
    def on_done(self, s):
        if s == -1: return

        hg_cmd = sorted(SUBLIMEHG_CMDS.keys())[s]
        alt_cmd_name, extra_prompt = SUBLIMEHG_CMDS[hg_cmd]

        fn = self.view.file_name()
        env = {"file_name": fn}

        if alt_cmd_name:
            
            if extra_prompt:
                env.update({"caption": extra_prompt, "fmtstr": alt_cmd_name,})
                self.view.run_command("hg_command_asking", env)
                return

            self.view.run_command("hg_cmd_line", {"cmd": alt_cmd_name % env})
        else:
            self.view.run_command("hg_cmd_line", {"cmd": hg_cmd})


class HgCommandAskingCommand(sublime_plugin.TextCommand):
    def run(self, 
    edit, caption='', fmtstr='', **kwargs):
        self.fmtstr = fmtstr
        self.content = kwargs
        if caption:
            self.view.window().show_input_panel(caption, '', self.on_done, None, None)
            return
        
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr % self.content})
    
    def on_done(self, s):
        self.content['input'] = s
        self.view.run_command("hg_cmd_line", {"cmd": self.fmtstr % self.content})
