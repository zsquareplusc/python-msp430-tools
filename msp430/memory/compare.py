#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""
This is a little tool to compare .a43, .text, .elf or binary
files.
"""

import sys
from io import BytesIO
import difflib
import msp430.memory


debug = False


def make_stream(memory):
    addresses = []
    stream = []
    for segment in sorted(list(memory.segments)):
        addresses.extend(range(segment.startaddress, segment.startaddress + len(segment.data)))
        stream.extend(bytearray(segment.data))
    return (addresses, stream)


def combine(addresses1, addresses2, data):
    for n, byte in enumerate(data):
        yield (
            addresses1[n] if addresses1 is not None else None,
            addresses2[n] if addresses2 is not None else None,
            byte)


def rows(addressed_data):
    stream = iter(addressed_data)
    while True:
        row = []
        a1, a2, data = next(stream)
        try:
            row.append(data)
            for i in range(1, 16):
                an1, an2, data = next(stream)
                row.append(data)
                if a1 is not None and an1 != a1 + i: break
                if a2 is not None and an2 != a2 + i: break
        finally:
            yield a1, a2, row


def write_row(prefix, address1, address2, row, output):
    values = ' '.join('{:02x}'.format(x) for x in row)
    ascii = ''.join(chr(x) if 32 <= x < 128 else '.' for x in row)
    # pad width
    values += ' ' * (47 - len(values))
    ascii += ' ' * (16 - len(values))
    # output line, insert gap at 8
    output.write('{} {:^8s} {:^8s}:  {} {}  {} {}\n'.format(
        prefix,
        '{:08x}'.format(address1) if address1 is not None else '--------',
        '{:08x}'.format(address2) if address2 is not None else '--------',
        values[:24], values[24:],
        ascii[:8], ascii[8:]))


def hexdump(prefix, addresses1, addresses2, data, output=sys.stdout):
    """\
    Print a hex dump.
    """
    for a1, a2, row in rows(combine(addresses1, addresses2, data)):
        write_row(prefix, a1, a2, row, output)


def compare(mem1, mem2, name1, name2, output=sys.stdout, show_equal=True):
    """\
    Compare and output hex dump of two memory object.
    :returns: True when files are identical, False otherwise.
    """

    addresses1, stream1 = make_stream(mem1)
    addresses2, stream2 = make_stream(mem2)

    s = difflib.SequenceMatcher(lambda x: x is None, stream1, stream2, autojunk=False)
    #~ sys.stderr.write('similarity [0...1]: {:.2f}\n'.format(s.ratio()))  # XXX if verbose
    equal = True
    for opcode, i1, i2, j1, j2 in s.get_opcodes():
        #~ print "=== %6s a[%d:%d] b[%d:%d]" % (opcode, i1, i2, j1, j2)
        if opcode == 'equal':
            if addresses1[i1] != addresses2[j1]:
                equal = False
            if show_equal:
                hexdump(' ', addresses1[i1:i2], addresses2[j1:j2], stream1[i1:i2], output)
            else:
                output.write('= {:08x} {:08x}:  {} bytes identical{}\n'.format(
                    addresses1[i1],
                    addresses2[j1],
                    i2 - i1,
                    ' at different addresses' if addresses1[i1] != addresses2[j1] else ''))
        elif opcode == 'insert':
            hexdump('+', None, addresses2[j1:j2], stream2[j1:j2], output)
            equal = False
        elif opcode == 'replace':
            #~ output.write('\n')
            hexdump('<', addresses1[i1:i2], None, stream1[i1:i2], output)
            #~ sys.stdout.write('--- is replaced with\n')
            hexdump('>', None, addresses2[j1:j2], stream2[j1:j2], output)
            #~ output.write('\n')
            equal = False
        elif opcode == 'delete':
            hexdump('-', addresses1[i1:i2], None, stream1[i1:i2], output)
            equal = False

    if equal:
        output.write("files are identical\n")
        return True
    else:
        return False


def inner_main():
    from optparse import OptionParser
    parser = OptionParser(usage="""\
%prog [options] FILE1 FILE2

Compare tool.

This tool reads binary, ELF or hex input files, creates a hex dump and shows
the differences between the files.
""")

    parser.add_option(
        '-o', '--output',
        dest='output',
        help='write result to given file',
        metavar='DESTINATION')

    parser.add_option(
        '-d', '--debug',
        dest='debug',
        help='print debug messages',
        default=False,
        action='store_true')

    parser.add_option(
        '-v', '--verbose',
        dest='verbose',
        help='print more details',
        default=False,
        action='store_true')

    parser.add_option(
        '-i', '--input-format',
        dest='input_format',
        help='input format name ({})'.format(', '.join(msp430.memory.load_formats)),
        default=None,
        metavar='TYPE')

    parser.add_option(
        '-a', '--show-all',
        dest='show_all',
        help='Do not hide equal parts',
        default=False,
        action='store_true')

    (options, args) = parser.parse_args()

    if options.input_format is not None and options.input_format not in msp430.memory.load_formats:
        parser.error('Input format {} not supported.'.format(options.input_format))

    global debug
    debug = options.debug

    output = sys.stdout
    if options.output:
        output = open(options.output, 'wb')

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
            sys.stderr.write('Loaded {} ({} segments)\n'.format(filename, len(mem)))

    same = compare(*(input_data + filenames), output=output, show_equal=options.show_all)
    sys.exit(not same)  # exit code 0 if same, otherwise 1


def main():
    try:
        inner_main()
    except SystemExit:
        raise                                   # let pass exit() calls
    except KeyboardInterrupt:
        #~ if debug: raise                         # show full trace in debug mode
        sys.stderr.write("User abort.\n")       # short messy in user mode
        sys.exit(1)                             # set error level for script usage
    except Exception as msg:                    # every Exception is caught and displayed
        if debug: raise                         # show full trace in debug mode
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg)  # short messy in user mode
        sys.exit(1)                             # set error level for script usage

if __name__ == '__main__':
    main()
