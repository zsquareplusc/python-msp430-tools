#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of https://github.com/zsquareplusc/python-msp430-tools
# (C) 2001-2017 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause
"""\
Helper functions to read and write TI-Text files.
"""

import msp430.memory
import msp430.memory.error


def load(filelike):
    """load data from a (opened) file in TI-Text format"""
    memory = msp430.memory.Memory()
    startAddr = 0
    segmentdata = bytearray()
    # TXT-File is parsed line by line
    for n, line in enumerate(filelike):
        if not line:
            break  # EOF
        l = line.strip()
        if l[0:1] == b'q':
            break
        elif l[0:1] == b'@':        # if @ => new address => send frame and set new addr.
            # create a new segment
            if segmentdata:
                memory.segments.append(msp430.memory.Segment(startAddr, segmentdata))
            startAddr = int(l[1:], 16)
            segmentdata = bytearray()
        else:
            for i in l.split():
                try:
                    segmentdata.append(int(i, 16))
                except ValueError as e:
                    raise msp430.memory.error.FileFormatError(
                            'File is no valid TI-Text: {}'.format(e),
                            filename=getattr(filelike, 'name', '<unknown>'),
                            lineno=n + 1)
    if segmentdata:
        memory.segments.append(msp430.memory.Segment(startAddr, segmentdata))
    return memory


def save(memory, filelike):
    """output TI-Text to given file object"""
    for segment in sorted(memory.segments):
        filelike.write('@{:04x}\n'.format(segment.startaddress).encode('ascii'))
        data = bytearray(segment.data)
        for i in range(0, len(data), 16):
            filelike.write('{}\n'.format(
                ' '.join(['{:02x}'.format(x) for x in data[i:i + 16]])
                ).encode('ascii'))
    filelike.write(b'q\n')
