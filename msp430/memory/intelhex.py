#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2001-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Helper functions to read and write intel hex files.
"""

import sys
import struct
import msp430.memory
import msp430.memory.error

def load(filelike):
    """load data from a (opened) file in Intel-HEX format"""
    memory = msp430.memory.Memory()
    segmentdata = bytearray()
    currentAddr = 0
    startAddr   = 0
    extendAddr  = 0
    for n, l in enumerate(filelike):
        if not l.strip(): continue  # skip empty lines
        if l[0:1] != b':': raise msp430.memory.error.FileFormatError(
                "line not valid intel hex data: '%s...'" % l[0:10],
                filename = getattr(filelike, "name", "<unknown>"),
                lineno = n+1)
        l = l.strip()               # fix CR-LF issues...
        length  = int(l[1:3], 16)
        address = int(l[3:7], 16) + extendAddr
        type    = int(l[7:9], 16)
        check   = int(l[-2:], 16)
        if type == 0x00:
            if currentAddr != address:
                if segmentdata:
                    memory.segments.append(msp430.memory.Segment(startAddr, segmentdata))
                startAddr = currentAddr = address
                segmentdata = bytearray()
            for i in range(length):
                segmentdata.append(int(l[9+2*i:11+2*i],16))
            currentAddr = length + currentAddr
        elif type == 0x02:
            extendAddr = int(l[9:13], 16) << 4
        elif type == 0x04 :
            extendAddr = int(l[9:13], 16) << 16
        elif type in (0x01, 0x03, 0x05):
            pass
        else:
            sys.stderr.write("Ignored unknown field (type 0x%02x) in ihex file.\n" % type)
    if segmentdata:
        memory.segments.append(msp430.memory.Segment(startAddr, segmentdata))
    return memory


def save(memory, filelike):
    """write a string containing intel hex to given file object"""
    for seg in sorted(memory.segments):
        address = seg.startaddress
        data = seg.data
        start = 0
        last_upper_address_bits = 0
        while start < len(data):
            # check for addresses >64k and output offset command when the value
            # changes
            upper_address_bits = address >> 16
            if last_upper_address_bits != upper_address_bits:
                filelike.write(_ihexline(address, struct.pack(">H", upper_address_bits), record_type=4))  # set offset
                last_upper_address_bits = upper_address_bits
            # write data line
            end = start + 16
            if end > len(data): end = len(data)
            filelike.write(_ihexline(address, data[start:end]))
            start += 16
            address += 16
    filelike.write(_ihexline(0, [], end=True))   # append no data but an end line


def _ihexline(address, buffer, end=False, record_type=0):
    """internal use: generate a line with intel hex encoded data"""
    out = []
    if end: # special override if end parameter is given
        record_type = 1
    out.append(':%02X%04X%02X' % (len(buffer), address & 0xffff, record_type))
    sum = len(buffer) + ((address >> 8) & 255) + (address & 255) + (record_type & 255)
    for b in buffer:
        out.append('%02X' % (b & 255))
        sum += b & 255
    out.append('%02X\r\n' % ( (-sum) & 255))
    return ''.join(out)

