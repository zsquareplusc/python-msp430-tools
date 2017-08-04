#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2010-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""
This is a little tool to compare .a43, .text, .elf or binary
files.
"""

import difflib
import sys

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

debug = False


# from https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(n, iterable, fillvalue=None):
    """grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"""
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def make_stream(memory, granularity=1):
    """create a list of bytes of length 'granularity' and a list of original addresses"""
    addresses = []
    stream = []
    for segment in sorted(list(memory.segments)):
        addresses.extend(range(segment.startaddress, segment.startaddress + len(segment.data), granularity))
        stream.extend(grouper(granularity, bytes(segment.data), fillvalue=0))
    return (addresses, stream)


def combine(addresses1, addresses2, data):
    """combine two address ranges (which may be None) and data"""
    for n, byte in enumerate(data):
        yield (
            addresses1[n] if addresses1 is not None else None,
            addresses2[n] if addresses2 is not None else None,
            byte)


def rows(addressed_data):
    """\
    iterate over dual-address and data sequence and make rows of up to
    16 data bytes, also restart rows if addresses jump.
    """
    stream = iter(addressed_data)
    while True:
        row = []
        a1, a2, data = next(stream)
        try:
            row.extend(bytearray(data))
            for i in range(len(data), 16, len(data)):
                an1, an2, data = next(stream)
                row.extend(bytearray(data))
                if a1 is not None and an1 != a1 + i: break
                if a2 is not None and an2 != a2 + i: break
        finally:
            yield a1, a2, row


def write_row(prefix, address1, address2, row, output):
    """output a hexdump line"""
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


def compare(mem1, mem2, name1, name2, output=sys.stdout, show_equal=True, granularity=1):
    """\
    Compare and output hex dump of two memory object.
    :returns: True when files are identical, False otherwise.
    """

    addresses1, stream1 = make_stream(mem1, granularity=granularity)
    addresses2, stream2 = make_stream(mem2, granularity=granularity)

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
                # XXX search for address jumps in the blocks just like hexdump does
                output.write('= {:08x} {:08x}:  {} bytes identical{}\n'.format(
                    addresses1[i1],
                    addresses2[j1],
                    (i2 - i1) * granularity,
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


def main():
    import msp430.commandline_helper

    class CompareTool(msp430.commandline_helper.CommandLineTool):
        description = """\
Compare tool.

This tool reads binary, ELF or hex input files and shows the differences
between the files a hex dump.
"""

        def configure_parser(self):
            group = self.parser_add_input(nargs=2)
            group.add_argument(
                '-g', '--granularity',
                type=int,
                default=1,
                help='compare x bytes at once, default: %(default)s')

            group = self.parser_add_output(textual=True)
            group.add_argument(
                '-a', '--show-all',
                help='Do not hide equal parts',
                default=False,
                action='store_true')

            self.parser_add_verbose()

        def run(self, args):
            input_data = []
            filenames = []
            for fileobj in args.SRC:
                mem = msp430.memory.load(fileobj.name, fileobj, args.input_format)
                input_data.append(mem)
                filenames.append(fileobj.name)

                if args.verbose:
                    sys.stderr.write('Loaded {} ({} segments)\n'.format(fileobj.name, len(mem)))

            same = compare(
                *(input_data + filenames),
                output=args.output,
                show_equal=args.show_all,
                granularity=args.granularity)
            sys.exit(not same)  # exit code 0 if same, otherwise 1

    CompareTool().main()


if __name__ == '__main__':
    main()
