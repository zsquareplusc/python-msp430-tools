#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Using the MSP430 JTAG parallel port board as SPI interface.

Requires Python 2+, ctypes and HIL.dll/libHIL.so
"""

import HIL
#~ import psyco
#~ psyco.full()

def init(port='1'):
    """open the parallel port and prepare for SPI mode"""
    HIL.Initialize(port)
    HIL.Connect()
    HIL.VCC(3000)
    HIL.TST(0)
    HIL.TCK(1)
    HIL.TDI(1)
    HIL.TMS(1)

def close():
    """close the parallel port"""
    HIL.Release()
    HIL.Close(1)

def _delay():
    """can be implemented if the SPI data rate has to be lowered"""
    #~ HIL.DelayMSec(1)
    #~ for i in range(10): HIL.DelayMSec(0)
    #~ HIL.DelayMSec(0)
    pass

def shift(data):
    """shift an binary string from/to the slave, returning the
       answer string of the same length
    """
    answer = []
    for character in data:
        shiftout = ord(character)
        indata = 0
        for i in range(8):
            HIL.TCK(0)
            HIL.TDI(shiftout & 0x80)
            shiftout <<= 1
            _delay()
            HIL.TCK(1)
            _delay()
            indata = (indata << 1) | HIL.ReadTDO()
        answer.append(chr(indata))
    return ''.join(answer)

def sync():
    """read untlil something else as a 0xff arrives.
    """
    while shift('\xff') != '\xff':
        pass

def getNullTeminated(maxlen=80):
    """read a null terminated string over SPI."""
    answer = []
    while maxlen:
        c = shift('\xff')
        if c == '\0': break
        answer.append(c)
        maxlen -= 1
    return ''.join(answer)


#test application
if __name__ == '__main__':
    import time
    init()
    #reset target
    HIL.RST(0)
    HIL.DelayMSec(10)
    HIL.RST(1)
    HIL.DelayMSec(10)
    
    #simple speed test
    bytes = 0
    t1 = time.time()
    for i in range(200):
        #~ print '%r' % getNullTeminated()
        bytes += len(getNullTeminated()) + 1
    dt = time.time() - t1
    print "%d bytes in %.2f seconds -> %.2f bytes/second" % (bytes, dt, bytes/dt)
