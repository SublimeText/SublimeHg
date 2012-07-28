"""simple client for the mercurial command server"""

import subprocess
import struct
import os

CH_DEBUG = 'd'
CH_ERROR = 'e'
CH_INPUT = 'I'
CH_LINE_INPUT = 'L'
CH_OUTPUT = 'o'
CH_RETVAL = 'r'


def start_server(hg_bin, repo_root, **kwargs):
	"""Returns a command server ready to be used."""
	startup_info = None
	if os.name == 'nt':
		startup_info = subprocess.STARTUPINFO()
		startup_info.dwFlags = subprocess.STARTF_USESHOWWINDOW

	return subprocess.Popen([hg_bin, "serve", "--cmdserver", "pipe",
							 "--repository", repo_root,
							 "--config", "ui.interactive=False"],
							 stdin=subprocess.PIPE,
							 stdout=subprocess.PIPE,
							 # If we don't redirect stderr and the server does
							 # not support an enabled extension, we won't be
							 # able to read stdout.
							 stderr=subprocess.PIPE,
							 startupinfo=startup_info)


def init_repo(root):
	subprocess.Popen("hg", "init", "--repository", root)


class CmdServerClient(object):
	def __init__(self, repo_root, hg_bin='hg'):
		self.hg_bin = hg_bin
		self.server = start_server(hg_bin, repo_root)
		self.read_greeting()

	def shut_down(self):
		self.server.stdin.close()

	def read_channel(self):
		# read channel name (1 byte) plus data length (4 bytes, BE)
		fmt = '>cI'
		ch, length = struct.unpack(fmt,
								   self.server.stdout.read(struct.calcsize(fmt)))
		assert len(ch) == 1, "Expected channel name of length 1."
		if ch in 'LI':
			raise NotImplementedError("Can't provide more data to server.")

		return ch, self.server.stdout.read(length)

	def read_greeting(self):
		_, ascii_txt = self.read_channel()
		assert ascii_txt, "Expected hello message from server."

		# Parse hello message.
		capabilities, encoding = ascii_txt.split('\n')
		self.encoding = encoding.split(':')[1].strip().lower()
		self.capabilities = capabilities.split(':')[1].strip().split()

		if not 'runcommand' in self.capabilities:
			raise EnvironmentError("Server doesn't support basic features.")

	def _write_block(self, data):
		# Encoding won't work well on Windows:
		# http://mercurial.selenic.com/wiki/CharacterEncodingOnWindows
		encoded_data = [x.encode(self.encoding) for x in data]
		encoded_data = '\0'.join(encoded_data)
		preamble = struct.pack(">I", len(encoded_data))
		self.server.stdin.write(preamble + encoded_data)
		self.server.stdin.flush()

	def run_command(self, cmd):
		self.server.stdin.write('runcommand\n')
		self._write_block(cmd)

	def receive_data(self):
		lines = []
		while True:
			channel, data = self.read_channel()
			if channel == CH_OUTPUT:
				lines.append(data.decode(self.encoding))
			elif channel == CH_RETVAL:
				return (''.join(lines)[:-1], struct.unpack(">l", data)[0])
			elif channel == CH_DEBUG:
				print "debug:", data
			elif channel == CH_ERROR:
				lines.append(data.decode(self.encoding))
				print "error:", data
			elif channel in (CH_INPUT, CH_LINE_INPUT):
				print "More data requested, can't satisfy."
				self.shut_down()
				return
			else:
				self.shut_down()
				print "Didn't expect such channel."
				return


if __name__ == '__main__':
	client = CmdServerClient("~/dev/foo")
	client.run_command(["help", "showconfig"])
	print client.receive_data()
	client.shut_down()
