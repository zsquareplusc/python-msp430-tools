#!/usr/bin/env python
"""
This is a little tool to compare .a43, .text, .elf or binary
files.

(C) 2010 Chris Liechti <cliechti@gmx.net>
this is distributed under a free software license, see LICENSE.txt.
"""

import sys
import os
import cStringIO
import difflib
import msp430.memory
import msp430.memory.hexdump


debug = False


def compare(mem1, mem2, name1, name2, output=sys.stdout, html=False):
    hexdumps = []
    for mem in (mem1, mem2):
        dump = cStringIO.StringIO()
        msp430.memory.hexdump.save(mem, dump)
        hexdumps.append(dump)

    # need lines for pythons difflib
    lines = [['%s\n' % x for x in f.getvalue().splitlines()] for f in hexdumps]

    n = 0
    if html:
        diff = difflib.HtmlDiff().make_file(lines[0], lines[1], name1, name2, numlines=n)
    else:
        diff = difflib.unified_diff(lines[0], lines[1], name1, name2, n=n)

    lines = list(diff)
    if len(lines):
        output.writelines(lines)
    else:
        output.write("files are identical\n")


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="""\
%prog [options] FILE FILE

Compare tool.

This tool reads binary, ELF or hex input files, creates a hex dump and shows
the differences between the files.
""")

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    parser.add_option("-d", "--debug",
            dest="debug",
            help="print debug messages",
            default=False,
            action='store_true')

    parser.add_option("-v", "--verbose",
            dest="verbose",
            help="print more details",
            default=False,
            action='store_true')

    parser.add_option("-i", "--input-format",
            dest="input_format",
            help="input format name (%s)" % (', '.join(msp430.memory.load_formats),),
            default="titext",
            metavar="TYPE")

    parser.add_option("--html",
            dest="html",
            help="create HTML output",
            default=False,
            action='store_true')

    (options, args) = parser.parse_args()

    if options.input_format not in msp430.memory.load_formats:
        parser.error('Input format %s not supported.' % (options.input_format))

    global debug
    debug = options.debug

    output = sys.stdout
    if options.output:
        output = open(options.output, 'w')

    if len(args) != 2:
        parser.error('expected exactly two arguments (files)')

    input_data = []
    filenames = []
    for filename in args:
        if filename == '-':                 # get data from stdin
            fileobj = sys.stdin
            filename = '<stdin>'
        else:
            fileobj = open(filename, "rb")  # or from a file

        mem = msp430.memory.load(filename, fileobj, options.input_format)
        input_data.append(mem)
        filenames.append(filename)

        if options.verbose:
            sys.stderr.write('Loaded %s (%d segments)\n' % (filename, len(mem)))

    compare(*(input_data + filenames), output=output, html=options.html)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise                                   # let pass exit() calls
    except KeyboardInterrupt:
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("User abort.\n")       # short messy in user mode
        sys.exit(1)                             # set error level for script usage
    except Exception, msg:                      # every Exception is caught and displayed
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg) # short messy in user mode
        sys.exit(1)                             # set error level for script usage
