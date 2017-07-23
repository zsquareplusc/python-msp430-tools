#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple converter for hex files.

data can be read from stdin and output on stdout:
usage: cat file.txt | convert - >out.a43
usage: convert file.txt >out.a43
usage: convert file.txt -o out.a43
"""

import argparse
import sys
import msp430.memory

debug = True


class BinaryFileType(object):
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


def inner_main():
    parser = argparse.ArgumentParser(usage="""\
%(prog)s [options] [INPUT...]

Simple hex file conversion tool.

It is also possible to specify multiple input files and create a single,
merged output.
""")

    group = parser.add_argument_group('Input')

    group.add_argument(
        'FILE',
        nargs='*',
        help='files to compare',
        type=BinaryFileType('r'))

    group.add_argument(
        '-i', '--input-format',
        help='input format name',
        choices=msp430.memory.load_formats,
        default=None,
        metavar='TYPE')

    group = parser.add_argument_group('Output')

    group.add_argument(
        '-o', '--output',
        type=argparse.FileType('w'),
        default='-',
        help='write result to given file',
        metavar='DESTINATION')

    group.add_argument(
        '-f', '--output-format',
        help='output_format format name',
        choices=msp430.memory.save_formats,
        default='titext',
        metavar='TYPE')

    parser.add_argument(
        '--develop',
        action='store_true',
        help='show tracebacks on errors (development of this tool)')

    args = parser.parse_args()
    #~ print(args)

    if not args:
        # if no files are given, read from stdin
        args = ['-']
        # default to TI-Text if no format is given
        if options.input_format is None:
            options.input_format = 'titext'

    global debug
    debug = args.develop

    # get input
    data = msp430.memory.Memory()          # prepare downloaded data

    for fileobj in args.FILE:
        data.merge(msp430.memory.load(fileobj.name, fileobj, args.input_format))

    # write ihex file
    msp430.memory.save(data, args.output, args.output_format)


def main():
    try:
        inner_main()
    except SystemExit:
        raise                                   # let pass exit() calls
    except KeyboardInterrupt:
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("User abort.\n")       # short messy in user mode
        sys.exit(1)                             # set error level for script usage
    except Exception as msg:                    # every Exception is caught and displayed
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg)  # short messy in user mode
        sys.exit(1)                             # set error level for script usage

if __name__ == '__main__':
    main()
