#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Parse TI's device.csv and output lines for msp430-mcu-list.txt.  The output is
not final, it has to manually pasted into the correct template sections in the
file (based on family and interrupt table size).
"""
import csv
import collections

# column names in the device.csv
msp430_device_info = collections.namedtuple('msp430_device_info', ('name', 'CPU_TYPE', 'CPU_Bugs', 'MPY_TYPE',
        'SBW', 'EEM', 'BREAKPOINTS', 'CLOCKCONTROL', 'CYCLECOUNTER', 'STACKSIZE',
        'RAMStart', 'RAMEnd', 'RAMStart2', 'RAMEnd2', 'USBRAMStart',
        'USBRAMEnd', 'MirrowedRAMSource', 'MirrowedRAMStart', 'MirrowRAMEnd',
        'BSLStart', 'BSLSize', 'BSLEnd', 'INFOStart', 'INFOSize', 'INFOEnd',
        'INFOA', 'INFOB', 'INFOC', 'INFOD', 'FStart', 'FEnd','FStart2',
        'FEnd2', 'Signature_Start', 'Signature_Size', 'INTStart', 'INTEnd'))

# create a mapping with all devices
devmap = {}

def numberify(x):
    """convert hex numbers, return original string on failure"""
    try:
        return int(x, 16)
    except ValueError:
        return x

# read the devices file
devices = csv.reader(open('../include/upstream/devices.csv', 'rb'))
for row in devices:
    #~ print row
    if not row or row[0][0] == '#': continue
    device = msp430_device_info(*([row[0].upper()] + [numberify(x) for x in row[1:]]))

    devmap[device.name] = (1 + device.INTEnd - device.INTStart), device, (device.FStart2 != 0)


# output devices in groups of the same vector table size, alphabetically sorted within each group.
last_vecsize = None
for vecsize, device, has_highmem in sorted(devmap.values()):
    # print group name if vector size changes (list is sorted by this)
    if last_vecsize != vecsize:
        last_vecsize = vecsize
        print "Vectors: %d" % vecsize
    # alter output depending on memory present above 64kB
    if has_highmem:
        print "    %-20s 0x%04x-0x%04x   0x%04x-0x%04x    0x%08x-0x%08x    # %dkB %dkB + %dkB = %dkB" % (
                device.name,
                device.RAMStart, device.RAMEnd,
                device.FStart, device.FEnd,
                device.FStart2, device.FEnd2,

                (1 + device.RAMEnd - device.RAMStart) / 1024,
                ((1 + device.FEnd - device.FStart) + (1 + device.INTEnd - device.INTStart)) / 1024,
                (1 + device.FEnd2 - device.FStart2) / 1024,
                ((1 + device.FEnd - device.FStart) + (1 + device.FEnd2 - device.FStart2) + (1 + device.INTEnd - device.INTStart)) / 1024,
                )

    else:
        print "    %-20s 0x%04x-0x%04x   0x%04x-0x%04x    # %dB %dkB" % (
                device.name,
                device.RAMStart, device.RAMEnd,
                device.FStart, device.FEnd,

                (1 + device.RAMEnd - device.RAMStart),
                ((1 + device.FEnd - device.FStart) + (1 + device.INTEnd - device.INTStart)) / 1024,
                )
