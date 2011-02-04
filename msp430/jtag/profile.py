#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Statistical profiler for the MSP430.

it works by sampling the address bus and counting addresses seen.
the problem there is, that it is not sure that we're reading a valid address
every time. an other issue is the relatively slow sampling rate compared to
the execution speed of the MCU, which means that several runs are need to
get meaningful numbers.
"""

from msp430.jtag import jtag
import sys
import os
import time

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage="%prog [OPTIONS]")

    parser.add_option("-v", "--verbose",
            dest="verbose",
            help="show more messages (can be given multiple times)",
            default=0,
            action='count')

    parser.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="FILENAME")

    (options, args) = parser.parse_args()

    # prepare output
    if options.output is None:
        output = sys.stdout
    else:
        output = open(options.output, 'w')

    jtag.init_backend(jtag.CTYPES_MSPGCC)   # doesn't currently work with 3'rd party libs
    samples = [0] * 2**16

    try:
        jtagobj = jtag.JTAG()

        if options.verbose:
            try:
                jtagobj.setDebugLevel(options.verbose)
            except IOError:
                sys.stderr.write("WARNING: Failed to set debug level in backend library\n")
            #~ memory.DEBUG = options.verbose
            jtag.DEBUG = options.verbose

        jtagobj.open()                          # try to open port
        try:
            jtagobj.connect()                   # try to connect to target
            connected = True
            jtagobj.reset(1, 0)
            sys.stderr.write("profiling... (CTRL-C to stop)\n")
            start_time = time.time()
            while True:
                samples[jtag.MSP430_readMAB()] += 1
        finally:
            stop_time = time.time()
            if sys.exc_info()[:1]:              # if there is an exception pending
                jtagobj.verbose = 0             # do not write any more messages
            if connected:
                jtagobj.reset(1, 1)             # reset and release target
            jtagobj.close()                     # release communication port
    except KeyboardInterrupt:
        # write out sample count per address
        total = 0
        for n, count in enumerate(samples):
            if count > 0:
                output.write("0x%04x\t%d\n" % (n, count))
            total += count
        # write a summary
        sys.stderr.write('%d samples in %.2f seconds (%d samples/second)\n' % (
                total,
                stop_time - start_time,
                total / (stop_time - start_time)))
