import sublime, sublime_plugin
import sys
import struct
import subprocess
import time
import os


class HGServer(object):
    def __init__(self):
        self.server = subprocess.Popen(
                                ["hg.bat", "serve", "--cmdserver", "pipe"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )

        # Receive greeting
        try:
            channel, data = self.read_data()
        except struct.error:
            err = self.server.stderr.read()
            raise EnvironmentError(err)
            self.shut_down()
        except EnvironmentError:
            raise
            self.shut_down()

        caps, enc = data.split('\n')
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


class HgCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.edit = edit
        self.view.window().show_input_panel('HGS command:', 'status', self.on_done, None, None)
    
    def on_done(self, s):
        old_cd = os.getcwd()
        os.chdir(os.path.dirname(self.view.file_name()))

        try:
            hgs = HGServer()
        except EnvironmentError, e:
            sublime.status_message("HGS:err:" + str(e))
            return

        try:
            data = hgs.run_command(s)
            p = self.view.window().get_output_panel('hgs')
            data = "Mercurial says...\n\n" + data
            p.insert(self.edit, 0, data)
            self.view.window().run_command('show_panel', {'panel': 'output.hgs'})
        except UnicodeDecodeError:
            print "Oops..."
        finally:
            hgs.shut_down()
            os.chdir(old_cd)
