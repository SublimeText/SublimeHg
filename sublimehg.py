import sublime, sublime_plugin
import sys
import struct
import subprocess
import time
import os

# XXX: Make async.

class HGServer(object):
    """I drive a command server (Mercurial>=1.9) whose protocol is described
    here: http://mercurial.selenic.com/wiki/CommandServer
    """
    def __init__(self, hg_exe='hg'):
        if os.name == 'nt':
            # Hide the child process window in Windows.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.server = subprocess.Popen(
                                [hg_exe, "serve", "--cmdserver", "pipe"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                startupinfo=startupinfo
                                )

        self.receive_greeting()
    
    def receive_greeting(self):
        try:
            channel, data = self.read_data()
        except struct.error:
            err = self.server.stderr.read()
            self.shut_down()
            raise EnvironmentError(err)
        except EnvironmentError:
            raise
            self.shut_down()

        try:
            caps, enc = data.split('\n')
        except ValueError:
            # Means the server isn't returnind the promised data, so the
            # environment is wrong.
            print "HGS:err: SublimeHG requires Mercurial>=1.9. (Probable cause.)"
            self.shut_down()
            raise EnvironmentError("SublimeHG requires Mercurial>=1.9")
            
        caps = ', '.join(caps.split()[1:])
        print "HGS:   :", "Capabilities:", caps
        print "HGS:   : Encoding:", enc.split()[1]

    def read_data(self):
        channel, length = struct.unpack('>cI', self.server.stdout.read(5))
        if channel in 'IL':
            return channel, length
        
        return channel, self.server.stdout.read(length)
    
    def write_block(self, cmd, *args):
        self.server.stdin.write(cmd + '\n')

        if args:
            data = '\0'.join(args) if len(args) > 1 else args[0]
            length = struct.pack('>l', len(data))
            self.server.stdin.write(length + data)
            self.server.stdin.flush()

    def run_command(self, *args):
        if len(args) == 1 and ' ' in args[0]:
            args = args[0].split()

        if args[0] == 'hg':
            args = args[1:]
            print "HGS:   : Stripped superfluous 'hg'"

        self.write_block('runcommand', *args)

        rv = ''
        while True:
            channel, line = self.read_data()
            if channel == 'o':
                rv += line
            elif channel == 'r':
                print "HGS:ret: %s" % struct.unpack('>l', line)[0]
                return rv[:-1]
            else:
                print "HGS:err: Most likely incomplete command was submitted."
                rv = "Could not complete operation. Was your command complete?"
                self.shut_down()
                return rv
    
    def get_encoding(self):
        self.write_block('getencoding')
        return self.read_data()[1]

    def shut_down(self):
        print "HGS: Shutting down HG server..."
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
            sublime.status_message("HGS:err:" + str(e))
            # hgs.shut_down()
            os.chdir(old_cd)
            return

        try:
            data = hgs.run_command(s)
            p = self.view.window().get_output_panel('hgs')
            data = "Mercurial says...\n\n" + data
            p.insert(self.edit, 0, data)
            self.view.window().run_command('show_panel', {'panel': 'output.hgs'})
        except UnicodeDecodeError, e:
            print "Oops (funny characters!)..."
            print e
        finally:
            hgs.shut_down()
            os.chdir(old_cd)


SUBLIMEHG_CMDS = [
    "add",
    "annotate",
    # "clone",
    "commit",
    "commit (this file)",
    "diff",
    # "export",
    # "forget",
    # "init",
    "log",
    "merge",
    "pull",
    "push",
    # "qdiff",
    # "qnew",
    # "qpop",
    # "qpush",
    # "qrefresh",
    # "remove",
    "serve",
    "status",
    "summary",
    "update",
]


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
            self.view.run_command("hg_commit", {"what": self.view.file_name()})
            return

        self.view.run_command("hg_cmd_line", {"cmd": SUBLIMEHG_CMDS[s]}) 


class HgCommit(sublime_plugin.TextCommand):
    def run(self, edit, what=''):
        self.what = what
        self.view.window().show_input_panel("Hg commit message:", '', self.on_done, None, None)
    
    def on_done(self, s):
        # XXX: This is bad.
        # msg = self.what.encode('ascii')
        self.view.run_command("hg_cmd_line", {"cmd":"commit %s -m '%s'" % (self.what, s)})
