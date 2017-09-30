#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2009-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""
This is a little tool to generate hex dumps from .a43, .text, .elf or binary
files. It can also read and frite hex dumps to Memory objects.
"""

import codecs
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


def hexdump(adr_data_tuple, output=sys.stdout):
    """\
    Print a hex dump.
    :param adr: address
    :param memstr: memory contents (bytes/string)
    :param output: file like object to write to
    """
    adr, memstr = adr_data_tuple
    # conversion to byte array only needed for python 2.xx as bytes would return
    # characters instead of ints
    for address, row in sixteen(adr, bytearray(memstr)):
        values = ' '.join('{:02x}'.format(x) for x in row)
        ascii = ''.join(chr(x) if (32 <= x < 128) else '.' for x in row)
        # pad width
        values += ' ' * (47 - len(values))
        ascii += ' ' * (16 - len(values))
        # output line, insert gap at 8
        output.write('{:08x}:  {} {}  {} {}\n'.format(
                address,
                values[:24], values[24:],
                ascii[:8], ascii[8:]))


def save(memory, filelike, is_text=False):
    """output a hexdump to given file object"""
    if not is_text:
        filelike = codecs.getwriter('ascii')(filelike)
    for n, segment in enumerate(sorted(memory.segments)):
        if n:
            filelike.write('........:\n')
        hexdump((segment.startaddress, segment.data), output=filelike)


def load(filelike):
    """\
    Read back a hex dump. As hex dumps can look different, only a subset of
    formats can be read. Its main purpose is to read the own format back.

    Note: The hex dump is decoded, the ASCII dump is required for correct
          decoding but is itself not decoded.
    """
    memory = msp430.memory.Memory()
    segmentdata = bytearray()
    segment_address = 0
    last_address = 0
    for n, line in enumerate(filelike):
        if not line.strip():
            continue  # skip empty lines
        if line.startswith(b'...'):
            continue  # skip marker lines
        try:
            adr, dump = line.split(b':', 1)
            address = int(adr, 16)
            if address != last_address:
                if segmentdata:
                    memory.segments.append(msp430.memory.Segment(segment_address, segmentdata))
                last_address = address
                segment_address = address
                segmentdata = bytearray()
            # We remove any whitespace and count the total number of chars to
            # find out how many digits there are. The ASCII dump is counted
            # too. The advantage of this method is that the gaps in the dump
            # and the space between hex and ASCII dump are irrelevant. The
            # drawback is that the ASCII dump needs to be present.

            # remove white space
            hex_data = dump.replace(b' ', b'')
            # find out how many digits are relevant
            digits = int(2 * len(hex_data) / 3)
            # take these and decode the hex data
            segmentdata.extend(int(hex_data[x:x + 2], 16) for x in range(0, digits, 2))
            # update address
            last_address += digits / 2
        except Exception as e:
            raise msp430.memory.error.FileFormatError(
                    'line not valid hex dump ({}) : {!r}'.format(e, line),
                    filename=getattr(filelike, 'name', '<unknown>'),
                    lineno=n + 1)
    if segmentdata:
        memory.segments.append(msp430.memory.Segment(segment_address, segmentdata))
    return memory


def main():
    import msp430.commandline_helper

    class HexDumpTool(msp430.commandline_helper.CommandLineTool):
        description = """\
Hexdump tool.

This tool generates hex dumps from binary, ELF or hex input files.

What is dumped?
- Intel hex and TI-Text: only data
- ELF: only segments that are programmed
- binary: complete file, address column is byte offset in file
"""

        def configure_parser(self):
            self.parser_add_input()
            self.parser_add_output(textual=True)
            self.parser_add_verbose()

        def run(self, args):
            for fileobj in args.SRC:
                mem = msp430.memory.load(fileobj.name, fileobj, args.input_format)
                if args.verbose:
                    args.output.write('{} ({} segments):\n'.format(fileobj.name, len(mem)))
                save(mem, args.output, is_text=True)

    HexDumpTool().main()

if __name__ == '__main__':
    main()
