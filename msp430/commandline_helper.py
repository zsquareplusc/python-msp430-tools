#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Helper to write command line interfaces.
"""

import argparse
import sys
import msp430
import msp430.memory


class BinaryFileType(object):
    """\
    handle binary files (filenames) and stdio ('-') like argparse.FileType
    but fix stdio for python 3.
    """
    def __init__(self, mode='r'):
        self._mode = mode

    def __call__(self, string):
        if self._mode not in 'rw':
            raise ValueError('invalid mode: {}'.format(self._mode))
        if string == '-':
            if self._mode == 'r':
                fileobj = sys.stdin
            else:
                fileobj = sys.stdout
            try:
                return fileobj.buffer   # Python 3
            except AttributeError:
                return fileobj          # Python 2
        try:
            return open(string, self._mode + 'b')
        except IOError as e:
            raise argparse.ArgumentTypeError('can not open "{}": {}'.format(string, e))

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, self._mode)



class CommandLineTool(object):
    """\
    Command line tool base class with some common functionality:
    - quickly add arguments for input and/or output
    - main that handles errors and hides tracebacks unless --develop is given
    """

    usage = '%(prog)s'

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter)
        self.args = None

    def parser_add_input(self, nargs='+'):
        """add arguments for hex file input and input format"""
        group = self.parser.add_argument_group('Input')

        group.add_argument(
            'SRC',
            nargs=nargs,
            help='filename or "-" for stdin',
            type=BinaryFileType('r'))

        group.add_argument(
            '-i', '--input-format',
            help='input format name',
            choices=msp430.memory.load_formats,
            default=None,
            metavar='TYPE')

        return group

    def parser_add_output(self, textual=False):
        """add arguments for one output and output format"""
        group = self.parser.add_argument_group('Output')

        group.add_argument(
            '-o', '--output',
            type=argparse.FileType('w') if textual else BinaryFileType('w'),
            default='-',
            help='write result to given file',
            metavar='DST')

        if not textual:
            group.add_argument(
                '-f', '--output-format',
                help='output_format format name',
                choices=msp430.memory.save_formats,
                default='titext',
                metavar='TYPE')

        return group

    def parser_add_verbose(self):
        """adds --verbose argument"""
        self.parser.add_argument(
            "-v", "--verbose",
            help="print more details",
            default=False,
            action='store_true')

    def parse_args(self):
        """add remaining arguments and parse sys.argv"""
        self.parser.add_argument(
            '--develop',
            action='store_true',
            help='show tracebacks on errors (development of this tool)')

        self.args = self.parser.parse_args()
        return self.args

    def main(self):
        """main that builds the argument parser, calls run() and handles errors"""
        try:
            self.configure_parser()
            self.parse_args()
            self.run(self.args)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            sys.stderr.write('User aborted.\n')
            sys.exit(1)
        except Exception as msg:
            if self.args is None or self.args.develop: raise
            sys.stderr.write('\nAn error occurred:\n{}\n'.format(msg))
            sys.exit(2)

    # ----- override in subclass -----

    def configure_parser(self):
        """update the argument parser here"""

    def run(self):
        """override this in actual tool"""
