#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2004-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Test File generator.

This tool generates a hex file, of given size, ending on address
0xffff if no start address is given.

USAGE: generate.py -l size_in_bytes
"""

from msp430 import memory
import struct
import random


def main():
    import msp430.commandline_helper

    class GeneratorTool(msp430.commandline_helper.CommandLineTool):
        description = """\
Test File generator.

This tool generates a hex file, of given size, ending on address
0xffff if no start address is given.
"""

        def configure_parser(self):
            group = self.parser.add_argument_group('Values')

            group.add_argument(
                "-l", "--length",
                help="number of bytes to generate",
                default=1024,
                type=int)

            group.add_argument(
                "-s", "--start-address",
                help="start address of data generated",
                default=None,
                type=int)

            group = group.add_mutually_exclusive_group()

            group.add_argument(
                "-c", "--count",
                help="use address as data",
                action="store_true",
                default=False)

            group.add_argument(
                "--const",
                help="use given 16 bit number as data (default=0x3fff)",
                default=0x3fff,  # JMP $
                type=int)

            group.add_argument(
                "--random",
                help="fill with random numbers",
                action="store_true",
                default=False)

            self.parser_add_output()

        def run(self, args):
            # get input
            mem = memory.Memory()          # prepare downloaded data

            # if no start address is given, align the data towards the end of the 64k
            # address room
            if args.start_address is None:
                args.start_address = 0x10000 - args.length

            # create data
            adresses = range(args.start_address, args.start_address + args.length, 2)
            if args.count:
                data = b''.join(struct.pack("<H", x & 0xffff) for x in adresses)
            elif args.random:
                data = b''.join(struct.pack("<H", random.getrandbits(16)) for x in adresses)
            else:
                data = b''.join(struct.pack("<H", args.const) for x in adresses)

            mem.append(memory.Segment(args.start_address, data))

            # write ihex file
            memory.save(mem, args.output, args.output_format)

    GeneratorTool().main()


if __name__ == '__main__':
    main()
