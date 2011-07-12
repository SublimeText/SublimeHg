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
            EnvironmentError(err)
            raise

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
            else:
                print "SublimeHg:err: " + line
                #  XXX Ask user for more input instead of blowing up.
                rv = "Could not complete operation. Was your command complete?"
                self.shut_down()
                return rv
    
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
SUBLIMEHG_CMDS = sorted([
    "add",
    "addremove",
    "annotate",
    "archive",
    "backout",
    "bisect",
    "bookmarks",
    "branch",
    "branches",
    "bundle",
    "cat",
    "clone",
    "commit",
    "commit (this file)",
    "copy",
    "diff",
    "export",
    "forget",
    "grep",
    "heads",
    "help",
    "identify",
    "import",
    "incoming",
    "init",
    "locate",
    "log",
    "manifest",
    "merge",
    "outgoing",
    "parents",
    "paths",
    "pull",
    "push",
    "recover",
    "remove",
    "rename",
    "resolve",
    "revert",
    "rollback",
    "root",
    "showconfig",
    "status",
    "summary",
    "tag",
    "tags",
    "tip",
    "unbundle",
    "update",
    "verify",
    "version"
    ])


class HgCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.edit = edit
        self.view.window().show_quick_panel(SUBLIMEHG_CMDS, self.on_done)
    
    def on_done(self, s):
        if s == -1: return

        if SUBLIMEHG_CMDS[s] == 'commit':
            self.view.run_command("hg_commit")
            return
        elif SUBLIMEHG_CMDS[s] == 'commit (this file)':
            fn = self.view.file_name()
            if not fn: return
            self.view.run_command("hg_commit", {"what": fn})
            return

        self.view.run_command("hg_cmd_line", {"cmd": SUBLIMEHG_CMDS[s]}) 


class HgCommit(sublime_plugin.TextCommand):
    def run(self, edit, what=''):
        self.what = what
        self.view.window().show_input_panel("Hg commit message:", '', self.on_done, None, None)
    
    def on_done(self, s):
        if ' ' in self.what:
            self.view.run_command("hg_cmd_line", {"cmd":"commit '%s' -m '%s'" % (self.what, s)})
            return
        self.view.run_command("hg_cmd_line", {"cmd":"commit %s -m '%s'" % (self.what, s)})
