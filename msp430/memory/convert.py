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

import msp430.memory.error
from msp430 import memory
import sys

debug = False

def inner_main():
    from optparse import OptionParser

    parser = OptionParser(usage="""\
%prog [options] [INPUT...]

Simple hex file conversion tool.

It is also possible to specify multiple input files and create a single,
merged output.
""")

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    parser.add_option("-i", "--input-format",
            dest="input_format",
            help="input format name (%s)" % (', '.join(memory.load_formats),),
            default=None,
            metavar="TYPE")

    parser.add_option("-f", "--output-format",
            dest="output_format",
            help="output format name (%s)" % (', '.join(memory.save_formats),),
            default="titext",
            metavar="TYPE")

    parser.add_option("-d", "--debug",
            dest="debug",
            help="print debug messages",
            default=False,
            action='store_true')

    (options, args) = parser.parse_args()

    if options.input_format is not None and options.input_format not in memory.load_formats:
        parser.error('Input format %s not supported.' % (options.input_format))

    if options.output_format not in memory.save_formats:
        parser.error('Output format %s not supported.' % (options.output_format))

    if not args:
        # if no files are given, read from stdin
        args = ['-']
        # default to TI-Text if no format is given
        if options.input_format is None:
            options.input_format = 'titext'

    global debug
    debug = options.debug

    # prepare output
    if options.output is None:
        try:
            out = sys.stdout.buffer #detach()
        except AttributeError:
            out = sys.stdout
    else:
        out = open(options.output, 'wb')

    # get input
    data = memory.Memory()          # prepare downloaded data

    for filename in args:
        if filename == '-':
            try:
                fileobj = sys.stdin.detach()
            except AttributeError:
                fileobj = sys.stdin
            data.merge(memory.load('<stdin>', fileobj, format=options.input_format))
        else:
            data.merge(memory.load(filename, format=options.input_format))

    # write ihex file
    memory.save(data, out, options.output_format)


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
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg) # short messy in user mode
        sys.exit(1)                             # set error level for script usage

if __name__ == '__main__':
    main()
