#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Test File generator.

This tool generates a hex file, of given size, ending on address
0xffff if no start address is given.

USAGE: generate.py -l size_in_bytes
"""

from msp430 import memory
import sys
import struct

from optparse import OptionParser

def main():
    parser = OptionParser(usage="""\
    %prog [options]

    Test File generator.

    This tool generates a hex file, of given size, ending on address
    0xffff if no start address is given.""")

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    parser.add_option("-f", "--output-format",
            dest="output_format",
            help="output format name (%s)" % (', '.join(memory.save_formats),),
            default="titext",
            metavar="TYPE")

    parser.add_option("-l", "--length",
            dest="size",
            help="number of bytes to generate",
            default=1024,
            type="int")

    parser.add_option("-s", "--start-address",
            dest="start_address",
            help="start address of data generated",
            default=None,
            type="int")

    parser.add_option("-c", "--count",
            dest="count",
            help="use address as data",
            action="store_true",
            default=False)

    parser.add_option("--const",
            dest="const",
            help="use given 16 bit number as data (default=0x3fff)",
            default=0x3fff, # JMP $
            type="int")

    (options, args) = parser.parse_args()

    if options.output_format not in memory.save_formats:
        parser.error('Output format %s not supported.' % (options.output_format))

    if args:
        parser.error('no arguments expected')

    # prepare output
    if options.output is None:
        out = sys.stdout
    else:
        out = file(options.output, 'wb')

    # get input
    mem = memory.Memory()          # prepare downloaded data

    # if no start address is given, align the data towards the end of the 64k
    # address room
    if options.start_address is None:
        options.start_address = 0x10000 - options.size

    # create data
    if options.count:
        data = ''.join([struct.pack("<H", x & 0xffff) 
                for x in xrange(options.start_address, options.start_address + options.size, 2)])
    else:
        data = ''.join([struct.pack("<H", options.const) 
                for x in xrange(options.start_address, options.start_address + options.size, 2)])

    mem.append(memory.Segment(options.start_address, data))

    # write ihex file
    memory.save(mem, out, options.output_format)


if __name__ == '__main__':
    main()
