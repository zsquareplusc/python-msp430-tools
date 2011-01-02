#!/usr/bin/env python
"""
This is a little tool to generate hex dumps from .a43, .text, .elf or binary
files.

(C) 2009-2010 Chris Liechti <cliechti@gmx.net>
this is distributed under a free software license, see LICENSE.txt.
"""

import sys
import msp430.memory

def sixteen(address, sequence):
    """A generator that yields sequences of 16 elements"""
    # yield tuples of (current_address, sequence_of_16_elements)
    row = []
    for x in sequence:
        row.append(x)
        if len(row) == 16:
            yield address, row
            del row[:]
            address += 16
    # and the rest if input's length was not a multiple of 16
    if row:
        yield address, row



def hexdump((adr, memstr), output=sys.stdout):
    """\
    Print a hex dump.
    :param adr: address
    :param memstr: memory contents (bytes/string)
    :param output: file like object to write to
    """
    for address, row in sixteen(adr, memstr):
        values = ' '.join("%02x" % ord(x) for x in row)
        ascii  = ''.join((32 <= ord(x) < 128) and x or '.' for x in row)
        # pad width
        values += ' '*(47 - len(values))
        ascii += ' '*(16 - len(values))
        # output line, insert gap at 8
        output.write("%08x:  %s %s  %s %s\n" % (
                address,
                values[:24], values[24:],
                ascii[:8], ascii[8:]))


def save(memory, filelike):
    """output a hexdump to given file object"""
    for n, segment in enumerate(sorted(memory.segments)):
        if n: filelike.write('........:\n')
        hexdump((segment.startaddress, segment.data), output=filelike)


def load(filelike):
    """\
    Read back a hex dump. As hex dumps can look different, only a subset of
    formats can be read. Its main purpose is to read the own format back.
    """
    memory = msp430.memory.Memory()
    segmentdata = []
    segment_address = 0
    last_address = 0
    for n, line in enumerate(filelike):
        if not line.strip(): continue  # skip empty lines
        if line.startswith('...'): continue  # skip marker lines
        try:
            adr, dump = line.split(':', 1)
            address = int(adr, 16)
            if address != last_address:
                if segmentdata:
                    memory.segments.append(msp430.memory.Segment(segment_address, ''.join(segmentdata)))
                last_address = address
                segment_address = address
                segmentdata = []
            # remove white space and take the first 2*16 hex digits
            hex_data = dump.replace(' ', '')
            # find out how many digits are relevant
            digits = 2 * len(hex_data) / 3
            segmentdata.append(hex_data[:digits].decode('hex'))
            last_address += digits / 2
        except Exception, e:
            raise msp430.memory.error.FileFormatError(
                    "line not valid hex dump (%s) : %r" % (e, line,),
                    filename = getattr(filelike, "name", "<unknown>"),
                    lineno = n+1)
    if segmentdata:
        memory.segments.append(msp430.memory.Segment(segment_address, ''.join(segmentdata)))
    return memory



debug = False

def main():
    from optparse import OptionParser
    parser = OptionParser(usage="""\
%prog [options] [SOURCE...]

Hexdump tool.

This tool generates hex dumps from binary, ELF or hex input files.

What is dumped?
- Intel hex and TI-Text: only data
- ELF: only segments that are programmed
- binary: complete file, address column is byte offset in file""")

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    parser.add_option("--debug",
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

    (options, args) = parser.parse_args()

    if not args:
        parser.error("missing object file name")

    if options.input_format not in msp430.memory.load_formats:
        parser.error('Input format %s not supported.' % (options.input_format))

    global debug
    debug = options.debug

    output = sys.stdout
    if options.output:
        output = open(options.output, 'w')

    for filename in args:
        if filename == '-':                 # get data from stdin
            fileobj = sys.stdin
            filename = '<stdin>'
        else:
            fileobj = open(filename, "rb")  # or from a file
        mem = msp430.memory.load(filename, fileobj, options.input_format)

        if options.verbose:
            output.write('%s (%d segments):\n' % (filename, len(mem)))

        save(mem, output)


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
