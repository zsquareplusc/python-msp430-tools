#!/usr/bin/env python
"""
This is a little tool to generate hex dumps from .a43, .text, .elf or binary
files.

Requires:
    Python 2.3+
    mspgcc extension library from http://mspgcc.sf.net

Chris <cliechti@gmx.net>
"""

import os, re, sys
import mspgcc.memory
import mspgcc.util

debug = False

def main():
    from optparse import OptionParser
    parser = OptionParser(usage="""\
%prog [options] [file|-]

Hexdump tool.

This tool generates hex dumps from binary, ELF or hex input files.

What is dumped?
- Intel hex and TI-Text: only data
- ELF: only segments that are programmed
- binary: complete file, address column is byte offset in file
""")

    parser = OptionParser()
    parser.add_option("-o", "--output", dest="output",
                      help="write result to given file", metavar="FILE",
                      default=None)
    parser.add_option("-d", "--debug", dest="debug",
                      help="print debug messages",
                      default=False, action='store_true')
    parser.add_option("-v", "--verbose", dest="verbose",
                      help="print more details",
                      default=False, action='store_true')
    parser.add_option("-b", "--binary",
                      dest="filetype", const="bin",
                      help="assume file(s) are binary",
                      default=False, action='store_const')
    parser.add_option("-i", "--ihex",
                      dest="filetype", const="ihex",
                      help="assume file(s) are intel hex",
                      default=False, action='store_const')
    parser.add_option("-t", "--titext",
                      dest="filetype", const="titext",
                      help="assume file(s) are TI-Text",
                      default=False, action='store_const')
    parser.add_option("-e", "--elf",
                      dest="filetype", const="elf",
                      help="assume file(s) are ELF objects",
                      default=False, action='store_const')

    (options, args) = parser.parse_args()

    if not args:
        parser.error("missing object file name")
    
    output = sys.stdout
    if options.output:
        output = open(options.output, 'w')

    for filename in args:
        data = mspgcc.memory.Memory()
        
        if options.filetype:                    # if the filetype is given...
            if filename == '-':                 # get data from stdin
                fileobj = sys.stdin
                filename = '<stdin>'
            else:
                fileobj = open(filename, "rb")  # or from a file
            if options.filetype == 'ihex':      # select load function
                data.loadIHex(fileobj)          # intel hex
            elif options.filetype == 'titext':
                data.loadTIText(fileobj)        # TI's format
            elif options.filetype == 'elf':
                data.loadELF(fileobj)           # ELF format
            elif options.filetype == 'bin':
                data.append(mspgcc.memory.Segment(0, fileobj.read()))
            else:
                raise ValueError("Illegal file type specified")
        else:                                   # no filetype given...
            if filename == '-':                 # for stdin:
                data.loadIHex(sys.stdin)        # assume intel hex
                filename = '<stdin>'
            elif filename:
                data.loadFile(filename)         # autodetect otherwise
        
        if options.verbose:
            output.write('%s (%d segments):\n' % (filename, len(data)))
        for n, segment in enumerate(data):
            if n: output.write('....:\n')
            mspgcc.util.hexdump((segment.startaddress, segment.data), output=output)


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
        sys.stderr.write("\nAn error occoured:\n%s\n" % msg) # short messy in user mode
        sys.exit(1)                             # set error level for script usage
