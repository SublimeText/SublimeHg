# coding: utf8

EOF = -1

class Lexer(object):
    def __init__(self, in_unicode):
        self.input = in_unicode
        self.index = 0
        self.c = self.input[self.index]

    def consume(self):
        self.index += 1
        if self.index >= len(self.input):
            self.c = EOF
        else:
            self.c = self.input[self.index]


class CommandLexer(Lexer):
    """
    cmd : NAME (OPTION string?)*
    """

    _white_space = ' \t'

    def __init__(self, in_unicode):
        Lexer.__init__(self, in_unicode)

    def _WHITE_SPACE(self):
        while self.c in self._white_space:
            self.consume()

    def _NAME(self):
        name_buf = []
        while self.c != EOF and self.c.isalpha():
            name_buf.append(self.c)
            self.consume()
        return ''.join(name_buf)

    def _OPTION(self):
        opt_buf = []
        while self.c != EOF and self.c == '-':
            opt_buf.append(self.c)
            self.consume()
        if self.c == EOF:
            SyntaxError("expected option name, got nothing")
        opt_buf.append(self._NAME())
        return ''.join(opt_buf)

    def _STRING(self):
        delimiter = self.c
        self.consume()
        str_buf = []
        while self.c != EOF:
            if self.c == '\\':
                str_buf.append(self.c)
                self.consume()
                if self.c == EOF or self.c not in (delimiter, '\\'):
                    SyntaxError("expected escape sequence, got '\\%s'" % self.c)
            str_buf.append(self.c)
            self.consume()
            if self.c == delimiter:
                self.consume()
                break
        return ''.join(str_buf)

    def __iter__(self):
        while self.c != EOF:
            if self.c in self._white_space:
                self._WHITE_SPACE()
            elif self.c.isalpha():
                yield self._NAME()
            elif self.c == '-':
                yield self._OPTION()
            elif self.c in '\'"':
                yield self._STRING()
        raise StopIteration


if __name__ == '__main__':
    # lx = Lexer(" foo")
    # while lx.c != EOF:
    #     print lx.c
    #     lx.consume()
    values = (
            "foo",
            "foo -b",
            "foo --bar",
            "foo -b -c",
            "foo -b 'this is a string'",
            "foo -b 'this is a string' --cmd \"whatever and ever\"",
            "foo -b 'this is \\'a string'",
            "foo -b 'mañana será otro día'",
        )
    for v in values:
        lx = CommandLexer(v)
        print v
        x = list([x for x in lx])
        print x
        print ' '.join(x)
