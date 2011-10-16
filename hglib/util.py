import itertools, cStringIO, error, os, subprocess

def grouper(n, iterable):
    ''' list(grouper(2, range(4))) -> [(0, 1), (2, 3)] '''
    args = [iter(iterable)] * n
    return itertools.izip(*args)

def eatlines(s, n):
    """
    >>> eatlines("1\\n2", 1)
    '2'
    >>> eatlines("1\\n2", 2)
    ''
    >>> eatlines("1\\n2", 3)
    ''
    >>> eatlines("1\\n2\\n3", 1)
    '2\\n3'
    """
    cs = cStringIO.StringIO(s)

    for line in cs:
        n -= 1
        if n == 0:
            return cs.read()
    return ''

def skiplines(s, prefix):
    """
    Skip lines starting with prefix in s

    >>> skiplines('a\\nb\\na\\n', 'a')
    'b\\na\\n'
    >>> skiplines('a\\na\\n', 'a')
    ''
    >>> skiplines('', 'a')
    ''
    >>> skiplines('a\\nb', 'b')
    'a\\nb'
    """
    cs = cStringIO.StringIO(s)

    for line in cs:
        if not line.startswith(prefix):
            return line + cs.read()

    return ''

def cmdbuilder(name, *args, **kwargs):
    """
    A helper for building the command arguments

    args are the positional arguments

    kwargs are the options
    keys that are single lettered are prepended with '-', others with '--',
    underscores are replaced with dashes

    keys with False boolean values are ignored, lists add the key multiple times

    None arguments are skipped

    >>> cmdbuilder('cmd', a=True, b=False, c=None)
    ['cmd', '-a']
    >>> cmdbuilder('cmd', long=True)
    ['cmd', '--long']
    >>> cmdbuilder('cmd', str='s')
    ['cmd', '--str', 's']
    >>> cmdbuilder('cmd', d_ash=True)
    ['cmd', '--d-ash']
    >>> cmdbuilder('cmd', _=True)
    ['cmd', '-']
    >>> cmdbuilder('cmd', list=[1, 2])
    ['cmd', '--list', '1', '--list', '2']
    >>> cmdbuilder('cmd', None)
    ['cmd']
    """
    cmd = [name]
    for arg, val in kwargs.items():
        if val is None:
            continue

        arg = arg.replace('_', '-')
        if arg != '-':
            arg = '-' + arg if len(arg) == 1 else '--' + arg
        if isinstance(val, bool):
            if val:
                cmd.append(arg)
        elif isinstance(val, list):
            for v in val:
                cmd.append(arg)
                cmd.append(str(v))
        else:
            cmd.append(arg)
            cmd.append(str(val))

    for a in args:
        if a is not None:
            cmd.append(a)

    return cmd

class reterrorhandler(object):
    """
    This class is meant to be used with rawcommand() error handler argument.
    It remembers the return value the command returned if it's one of allowed
    values, which is only 1 if none are given. Otherwise it raises a CommandError.

    >>> e = reterrorhandler('')
    >>> bool(e)
    True
    >>> e(1, 'a', '')
    'a'
    >>> bool(e)
    False
    """
    def __init__(self, args, allowed=None):
        self.args = args
        self.ret = 0
        if allowed is None:
            self.allowed = [1]
        else:
            self.allowed = allowed

    def __call__(self, ret, out, err):
        self.ret = ret
        if ret not in self.allowed:
            raise error.CommandError(self.args, ret, out, err)
        return out

    def __nonzero__(self):
        """ Returns True if the return code was 0, False otherwise """
        return self.ret == 0

close_fds = os.name == 'posix'

startupinfo = None
if os.name == 'nt':
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

def popen(args, env={}):
    environ = None
    if env:
        environ = dict(os.environ)
        environ.update(env)

    return subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, close_fds=close_fds,
                            startupinfo=startupinfo, env=environ)
