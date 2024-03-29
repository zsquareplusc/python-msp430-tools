#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2001-2010 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Simple C preprocessor (almost). It is not fully compliant to a real
ANSI C preprocessor, but it understands a helpful subset.
"""

# TODO:
# - stringify #
# - it isn't fully compatible to a real cpp

import sys
import os
import re
import logging
import binascii
import codecs
from msp430.asm import infix2postfix
from msp430.asm import rpn


def hexlify(text):
    return binascii.hexlify(text.encode('utf-8')).decode('utf-8')


def line_joiner(line_iterator):
    """\
    Given a readline function, return lines, but handle line continuations
    ('\\\n'). When lines are joined, the same number of blank lines is output
    so that the line counter for the consumer stays correct.
    """
    while True:
        joined_line = '\\\n'
        joined_lines = 0
        while joined_line[-2:] == '\\\n':
            joined_line = joined_line[:-2]
            line = next(line_iterator)
            if not line:
                break
            joined_line += line.rstrip() + '\n'  # XXX drops spaces too
            joined_lines += 1
        while joined_lines > 1:
            yield '\n'
            joined_lines -= 1
        if not joined_line:
            break
        yield joined_line


class PreprocessorError(Exception):
    """Preprocessor specific errors"""


class Scanner(infix2postfix.Scanner):
    scannerRE = re.compile(r'''
       (?P<SPACE>           \s+             ) |
       (?P<LEFT>            \(              ) |
       (?P<RIGHT>           \)              ) |
       (?P<HEXNUMBER>       0x[0-9a-f]+     ) |
       (?P<BINNUMBER>       0b[0-9a-f]+     ) |
       (?P<NUMBER>          \d+             ) |
       (?P<UNARYOPERATOR>   defined|!|(\B[-+~]\b)   ) |
       (?P<OPERATOR>        \|\||&&|<<|>>|==|!=|<=|>=|[-+*/\|&\^<>] ) |
       (?P<VARIABLE>        \.?[$_a-z]\w*   )
    ''', re.VERBOSE | re.IGNORECASE | re.UNICODE)

cpp_precedence_list = [
    # lowest precedence
    ['||', 'or'],
    ['&&', 'and'],
    ['|', '^', '&'],
    ['==', '!='],
    ['<', '<=', '>', '>='],
    ['<<', '>>'],
    ['+', '-'],
    ['*', '/', '%'],
    ['!', 'not'],
    ['~', 'neg', '0 +'],
    ['defined'],
    ['(', ')'],
    # highest precedence
]

precedence = infix2postfix.convert_precedence_list(cpp_precedence_list)


class Undefined(object):
    def __int__(self):
        return 0

    def __str__(self):
        return ''

    def __repr__(self):
        return '<UNDEFINED>'
undefined = Undefined()


class Evaluator(rpn.RPN):
    """\
    An RPN calculator with infix to postfix converter, so that expressions for
    #if can be evaluated.
    """
    re_defined_translation = re.compile(r'LOOKUP (\w+?) defined')

    def __init__(self):
        rpn.RPN.__init__(self)
        self.defines = {}
        # add some aliases for logic operators
        self.builtins['!'] = self.builtins['not']
        self.builtins['&&'] = self.builtins['and']
        self.builtins['||'] = self.builtins['or']

    def _translate_defined(self, match):
        return u'DEFINED {}'.format(match.group(1))

    @rpn.word('LOOKUP')
    def word_LOOKUP(self, stack):
        key = self.next_word()
        #~ print "LOOKUP", key
        if key in self.defines:
            try:
                backup = self[:]
                value = self.eval(self.defines[key])
                self[:] = backup  # XXX better way to do this
                self.push(value)
            except Exception:
                #~ print "RPN eval failed using directly: %r %r %s" % (key, self.defines[key], e) # XXX debug
                self.push(self.defines[key])
        else:
            self.push(undefined)
        #~ print "LOOKUP %r %r" % (key, self[-1])

    @rpn.word('DEFINED')
    def word_DEFINED(self, stack):
        key = self.next_word()
        self.push(key in self.defines)

    def eval(self, expression):
        self.clear()
        try:
            rpn_expr = infix2postfix.infix2postfix(
                    expression,
                    scanner=Scanner,
                    precedence=precedence,
                    variable_prefix='LOOKUP ')
        except ValueError:
            raise PreprocessorError('error in expression: {!r}'.format(expression))
        #~ print "RPN: %r" % (rpn_expr,) # XXX debug
        # hack: replace "LOOKUP <word> DEFINED" with "DEFINED <word>"
        rpn_expr = self.re_defined_translation.sub(self._translate_defined, rpn_expr)
        self.interpret_sequence(rpn_expr.split(' '))
        if len(self) != 1:
            raise PreprocessorError('error in expression: {!r} stack: {}'.format(expression, self))
        return self.pop()


class AnnoatatedLineWriter(object):
    """\
    Write lines to the output. If line numbers jump also write out an
    information line with line number and filename: '# nn "filename"'
    """
    def __init__(self, output, filename):
        self.output = output
        self.filename = filename
        self.marker = None

    def write(self, lineno, text):
        """
        Write line. It is expected to be called with lines only (ending in
        '\n') otherwise will the markers be misplaced.
        """
        # emit line number and file hints for the next stage
        if self.marker != lineno:
            self.output.write('# {} "{}"\n'.format(lineno, self.filename))
        self.marker = lineno + 1
        try:
            self.output.write(text)
        except IOError:
            raise EOFError()


class Preprocessor(object):
    """\
    A text processing tool like a C Preprocessor. However it is not 100%
    compatible to a C Preprocessor.
    """

    re_scanner = re.compile(r'''
            (?P<MACRO>      ^[\t ]*\#[\t ]*define[\t ]+(?P<MACRO_NAME>\w+)\((?P<MACRO_ARGS>.*?)\)(?P<MACRO_DEF>[\t ]+(.+))? ) |
            (?P<DEFINE>     ^[\t ]*\#[\t ]*define[\t ]+(?P<DEF_NAME>\w+)([\t ]+)?(?P<DEF_VALUE>.+)?     ) |
            (?P<INCLUDE>    ^[\t ]*\#[\t ]*include[\t ]+[<"](?P<INC_NAME>[\w\\/\.]+)[">]  ) |
            (?P<PRAGMA>     ^[\t ]*\#[\t ]*pragma($|[\t ]+.*)                   ) |
            (?P<MESSAGE>    ^[\t ]*\#[\t ]*message($|[\t ]+.*)                  ) |
            (?P<WARNING>    ^[\t ]*\#[\t ]*warning($|[\t ]+.*)                  ) |
            (?P<ERROR>      ^[\t ]*\#[\t ]*error($|[\t ]+.*)                    ) |
            (?P<IF>         ^[\t ]*\#[\t ]*if[\t ]+(?P<IF_EXPR>.*)              ) |
            (?P<ELIF>       ^[\t ]*\#[\t ]*elif[\t ]+(?P<ELIF_EXPR>.*)          ) |
            (?P<IFDEF>      ^[\t ]*\#[\t ]*ifdef[\t ]+(?P<IFDEF_NAME>.*)        ) |
            (?P<IFNDEF>     ^[\t ]*\#[\t ]*ifndef[\t ]+(?P<IFNDEF_NAME>.*)      ) |
            (?P<ELSE>       ^[\t ]*\#[\t ]*else                                 ) |
            (?P<ENDIF>      ^[\t ]*\#[\t ]*endif                                ) |
            (?P<UNDEF>      ^[\t ]*\#[\t ]*undef[\t ]+(?P<UNDEF_NAME>.*)        ) |
            (?P<NONPREPROC> ^[^\#].*         )
            ''', re.VERBOSE | re.UNICODE)

    re_silinecomment = re.compile(r'(//).*')
    re_inlinecomment = re.compile(r'/\*.*?\*/')
    re_macro_usage = re.compile(r'(?P<MACRO>\w+)[\t ]*\((?P<ARGS>.*?)\)', re.UNICODE)
    re_splitter = re.compile(r'''
            (?P<STRING>     "([^"\\]*?(\\.[^"\\]*?)*?)"     ) |
            (?P<WORD>       \w+         ) |
            (?P<NONWORD>    [^"\w]+       )
            ''', re.VERBOSE | re.UNICODE)

    def __init__(self):
        self.macros = {}
        self.log = logging.getLogger('cpp')
        self.namespace = Evaluator()
        self.include_path = ['.']

    def _apply_macro(self, match_obj):
        name = match_obj.group('MACRO')
        if name in self.macros:
            values = [x.strip() for x in match_obj.group('ARGS').split(',')]
            args, expansion = self.macros[name]
            if len(args) != len(values):
                raise PreprocessorError('Macro invocation with wrong number of parameters. Expected {} got {}: {!r}'.format(
                        len(args), len(values), values))
            self.expansion_done = True
            return expansion % dict(zip(args, values))
        else:
            return match_obj.group(0)   # nothing of ours, return original

    def expand(self, line):
        """Expand object and function like macros in given line."""
        recusion_limit = 10
        self.expansion_done = True
        while self.expansion_done and recusion_limit:
            # replace function like macros
            self.expansion_done = False
            line = self.re_macro_usage.sub(self._apply_macro, line)
            # replace object like macros
            pos = 0
            res = []
            while pos < len(line):
                m = self.re_splitter.match(line, pos)
                if m is None:
                    raise PreprocessorError(u'No match in macro replacement code: {!r}...'.format(
                        line[pos:pos + 10],))
                pos = m.end()
                token_type = m.lastgroup
                if token_type in ('STRING', 'NONWORD', 'OTHER'):
                    word = m.group(token_type)
                    res.append(word)
                elif token_type == 'WORD':
                    word = m.group(token_type)
                    if word in self.namespace.defines:
                        res.append(self.namespace.defines[word])
                        self.expansion_done = True
                    else:
                        res.append(word)
                else:
                    raise PreprocessorError(u'No match in macro replacement code: {!r}...'.format(
                        line[pos:pos + 10],))
            line = ''.join(res)
            recusion_limit -= 1
        if recusion_limit == 0:
            self.log.error('recursive define, stopped expansion: {!r} '.format(line))
        #~ print "expand -> %r" % (res)          #DEBUG
        return line.replace('##', '')

    def preprocess(self, infile, outfile, filename, include_callback=None):
        """Scan lines and process preprocessor directives"""
        self.log.info("processing {}".format(filename))
        error_found = False
        empty_lines = 0
        process = True
        my_if_was_not_hidden = False
        if_name = '<???>'
        hiddenstack = []
        in_comment = False
        writer = AnnoatatedLineWriter(outfile, filename)
        line = ''
        lineno = 0
        try:
            for line in line_joiner(iter(infile)):
                lineno += 1
                #~ print "|", line.rstrip()
                line = self.re_inlinecomment.sub('', line)  # .strip()
                if in_comment:
                    p = line.find('*/')
                    if p >= 0:
                        in_comment = False
                        line = line[p + 2:]
                        if not line.strip():
                            continue
                    else:
                        continue
                #~ line = line.rstrip()
                line = self.re_silinecomment.sub('', line)
                #~ print ">", line
                if not in_comment:
                    p = line.find('/*')
                    if p >= 0:
                        in_comment = True
                        line = line[:p]
                        if not line.strip():
                            continue
                #~ if not line.strip(): continue

                m = self.re_scanner.match(line)
                if m is None:
                    raise PreprocessorError("error: invalid preprocessing directive: {!r}".format(line))
                elif m.lastgroup == 'IF':
                    expression = m.group('IF_EXPR')
                    value = self.namespace.eval(expression)
                    self.log.debug("#if {!r} -> {!r}".format(expression, value))
                    hiddenstack.append((process, my_if_was_not_hidden, if_name, False))
                    if_name = expression
                    if process:
                        process = value
                        my_if_was_not_hidden = True
                    else:
                        my_if_was_not_hidden = False
                    continue
                elif m.lastgroup == 'ELIF':
                    # do what #else would do
                    if my_if_was_not_hidden:
                        process = not process
                    # then do what #if would do
                    expression = m.group('ELIF_EXPR')
                    value = self.namespace.eval(expression)
                    self.log.debug("#elif {!r} -> {!r}".format(expression, value))
                    # replace state on the stack
                    hiddenstack.append((process, my_if_was_not_hidden, if_name, True))
                    if_name = expression
                    if process:
                        process = value
                        my_if_was_not_hidden = True
                    else:
                        my_if_was_not_hidden = False
                    continue
                elif m.lastgroup == 'IFDEF':
                    symbol = m.group('IFDEF_NAME').strip()
                    value = symbol in self.namespace.defines
                    self.log.debug("#ifdef {!r} -> {!r}".format(symbol, value))
                    hiddenstack.append((process, my_if_was_not_hidden, if_name, False))
                    if_name = symbol
                    if process:
                        process = value
                        my_if_was_not_hidden = True
                    else:
                        my_if_was_not_hidden = False
                    continue
                elif m.lastgroup == 'IFNDEF':
                    symbol = m.group('IFNDEF_NAME').strip()
                    value = symbol not in self.namespace.defines
                    self.log.debug("#ifndef {!r} -> {!r}".format(symbol, value))
                    hiddenstack.append((process, my_if_was_not_hidden, if_name, False))
                    if_name = symbol
                    if process:
                        process = value
                        my_if_was_not_hidden = True
                    else:
                        my_if_was_not_hidden = False
                    continue
                elif m.lastgroup == 'ELSE':
                    self.log.debug("#else {!r}".format(if_name))
                    if my_if_was_not_hidden:
                        process = not process
                    continue
                elif m.lastgroup == 'ENDIF':
                    self.log.debug("#endif {!r}".format(if_name))
                    while True:
                        (process, my_if_was_not_hidden, if_name, implicit_endif) = hiddenstack.pop()
                        if not implicit_endif:
                            break
                    continue
                elif not process:
                    continue
                elif m.lastgroup == 'INCLUDE':
                    include_name = m.group('INC_NAME')
                    self.log.debug('including "{}"'.format(include_name))
                    for location in self.include_path:
                        path = os.path.normpath(os.path.join(location, include_name))
                        if os.path.exists(path):
                            if include_callback is not None:
                                include_callback(path)
                            self.preprocess(codecs.open(path, 'r', 'utf-8'), outfile, path, include_callback)
                            writer.marker = None  # force marker output
                            break
                    else:
                        raise PreprocessorError('include file {!r} not found'.format(include_name))
                    continue
                elif m.lastgroup == 'MACRO':
                    name = m.group('MACRO_NAME')
                    args = [x.strip() for x in m.group('MACRO_ARGS').split(',')]
                    if m.group('MACRO_DEF'):
                        definition = m.group('MACRO_DEF').strip()
                    else:
                        definition = ''
                    if name in self.macros:
                        self.log.warn("{!r} redefinition ignored".format(name))
                    else:
                        # prepare the macro value to be used as format string
                        # (python's % operator)
                        definition = definition.replace('%', '%%')
                        for arg in args:
                            definition = re.sub(
                                    r'(^|[^\w_])#({})([^\w_]|$)'.format(arg),
                                    r'\1"%({})s"\3'.format(hexlify(arg)),
                                    definition)
                            definition = re.sub(
                                    r'(^|[^\w_])({})([^\w_]|$)'.format(arg),
                                    r'\1%({})s\3'.format(hexlify(arg)),
                                    definition)
                        self.macros[name] = ([hexlify(x) for x in args], definition)
                        self.log.debug("defined macro {!r} => {!r}".format(name, self.macros[name]))
                    continue
                elif m.lastgroup == 'DEFINE':
                    symbol = m.group('DEF_NAME')
                    if m.group('DEF_VALUE'):
                        definition = m.group('DEF_VALUE').strip()
                    else:
                        definition = ''
                    if symbol in self.namespace.defines:
                        self.log.warn("{!r} redefinition ignored".format(symbol))
                    else:
                        self.namespace.defines[symbol] = definition
                        self.log.debug("defined {!r} => {!r}".format(symbol, self.namespace.defines[symbol]))
                    continue
                elif m.lastgroup == 'UNDEF':
                    symbol = m.group('UNDEF_NAME').strip()
                    self.log.debug("undefined {}".format(symbol))
                    del self.namespace.defines[symbol]
                    continue
                elif m.lastgroup == 'MESSAGE':
                    sys.stderr.write(u'{}:{}: message: {}\n'.format(
                            filename,
                            lineno,
                            line.strip(),))
                    continue
                elif m.lastgroup == 'WARNING':
                    sys.stderr.write(u'{}:{}: warning: {}\n'.format(
                            filename,
                            lineno,
                            line.strip(),))
                    continue
                elif m.lastgroup == 'ERROR':
                    sys.stderr.write(u'{}:{}: error: {}\n'.format(
                            filename,
                            lineno,
                            line.strip(),))
                    error_found = True
                    continue
                elif m.lastgroup == 'PRAGMA':
                    pass  # => line will be output below
                elif m.lastgroup == 'NONPREPROC':
                    line = self.expand(line)
                else:
                    raise PreprocessorError('Invalid input: {!r}'.format(line))

                if not line.strip():
                    empty_lines += 1
                    if empty_lines > 1:
                        continue
                else:
                    empty_lines = 0
                writer.write(lineno, line)
            # at the end of the loop, check if there were unbalanced #if's
            if hiddenstack:
                raise PreprocessorError('missing #endif')

        except PreprocessorError as e:
            # annotate exception with location in source file
            e.line = lineno
            e.filename = filename
            e.text = line
            self.log.info('error while processing "{}"'.format(line.strip()))
            raise
        except:
            self.log.info('error while processing "{}"'.format(line.strip()))
            raise
        else:
            self.log.info('done "{}"'.format(filename))
        return error_found


class Discard(object):
    """File like target object that consumes and discards all data"""
    def write(self, s):
        """dummy write"""


def main():
    import sys
    import argparse
    logging.basicConfig()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'SOURCE',
        type=argparse.FileType('r'),
        nargs='?',
        default='-')

    group = parser.add_argument_group('Input')

    group.add_argument(
        '-p', '--preload',
        help='process this file first. its output is discarded but definitions are kept.',
        metavar='FILE')

    group.add_argument(
        '-D', '--define',
        action='append',
        dest='defines',
        metavar='SYM[=VALUE]',
        default=[],
        help='define symbol')

    group.add_argument(
        '-I', '--include-path',
        action='append',
        metavar='PATH',
        default=[],
        help='Add directory to the search path list for includes')

    group = parser.add_argument_group('Output')

    group.add_argument(
        '-o', '--outfile',
        type=argparse.FileType('w'),
        help='name of the destination file',
        default='-',
        metavar='FILE')

    parser.add_argument(
        '--dependency-scan',
        action='store_true',
        default=False,
        help='just print names of includes, not actual content')

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help='print status messages to stderr')

    parser.add_argument(
        '--develop',
        action='store_true',
        default=False,
        help='print debug messages to stderr')

    args = parser.parse_args()

    if args.develop:
        logging.getLogger('cpp').setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger('cpp').setLevel(logging.INFO)
    else:
        logging.getLogger('cpp').setLevel(logging.WARN)

    cpp = Preprocessor()
    # extend include search path
    # built in places for msp430.asm
    d = os.path.join(os.path.dirname(sys.modules['msp430.asm'].__file__), 'include')
    cpp.include_path.append(d)
    cpp.include_path.append(os.path.join(d, 'upstream'))
    # user provided directories (-I)
    cpp.include_path.extend(args.include_path)
    # insert predefined symbols (XXX function like macros not yet supported)
    for definition in args.defines:
        if '=' in definition:
            symbol, value = definition.split('=', 1)
        else:
            symbol, value = definition, '1'
        cpp.namespace.defines[symbol] = value

    # process files now
    if args.preload:
        cpp.preprocess(open(args.preload), Discard(), args.preload)

    if args.dependency_scan:
        # add a callback that writes out filenames of includes
        # remember outfile as we're changing it below
        def print_include(path, outfile=args.outfile):
            outfile.write('{}\n'.format(path))
        args.outfile = Discard()  # discard following output
    else:
        print_include = None

    try:
        error_found = cpp.preprocess(args.SOURCE, args.outfile, args.SOURCE.name, print_include)
        if error_found:
            sys.exit(2)
    except PreprocessorError as e:
        sys.stderr.write(u'{e.filename}:{e.line}: {e}\n'.format(e=e))
        if args.develop:
            if hasattr(e, 'text'):
                sys.stderr.write(u'{e.filename}:{e.line}: input line: {e.text!r}\n'.format(e=e))
        sys.exit(1)


if __name__ == '__main__':
    main()
