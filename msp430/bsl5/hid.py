#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple MSP430 BSL implementation using the USB HID interface.
"""

import sys
import os
from msp430.bsl5 import bsl5
import struct
import logging
import time
import pkgutil

from optparse import OptionGroup
import msp430.target
import msp430.memory
from cStringIO import StringIO




class HIDBSL5(bsl5.BSL5):
    """\
    Implementation of the BSL protocol over the serial port.
    """

    def __init__(self):
        bsl5.BSL5.__init__(self)
        self.hid_device = None
        self.logger = logging.getLogger('BSL5')

    def open(self, device):
        self.logger.info('Opening HID device %r' % (device,))
        self.hid_device = os.open(device, os.O_RDWR)

    def __del__(self):
        self.close()

    def close(self):
        """Close serial port"""
        if self.hid_device is not None:
            self.logger.info('closing HID device')
            try:
                os.close(self.hid_device)
            except:
                self.logger.exception('error closing device:')
            self.hid_device = None


    def bsl(self, cmd, message='', expect=None, receive_response=True):
        """\
        Low level access to the HID communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer. The first byte will be the response code from the BSL

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, the answer is just returned.

        Frame format:
        +------+-----+-----------+
        | 0x3f | len | D1 ... DN |
        +------+-----+-----------+
        """
        # first synchronize with slave
        self.logger.debug('Command 0x%02x %s (%d bytes)' % (cmd, message.encode('hex'), 1+len(message)))
        txdata = struct.pack('<BBB', 0x3f, 1+len(message), cmd) + message
        txdata += '\xac'*(64 - len(txdata)) # pad up to block size
        #~ self.logger.debug('Sending command: %r %d Bytes' % (txdata.encode('hex'), len(txdata)))
        # transmit command
        os.write(self.hid_device, txdata)
        if receive_response:
            self.logger.debug('Reading answer...')
            report = os.read(self.hid_device, 64)
            self.logger.debug('report = %r' % report.encode('hex'))
            pi = report[0]
            if pi == '\x3f':
                length = ord(report[1])
                data = report[2:2+length]
                #~ if expect is not None and len(data) != expect:
                    #~ raise bsl5.BSL5Error('expected %d bytes, got %d bytes' % (expect, len(data)))
                return data
            else:
                if pi: raise bsl5.BSL5Error('received bad PI, expected 0x3f (got 0x%02x)' % (ord(pi),))
                raise bsl5.BSL5Error('received bad PI, expected 0x3f (got empty response)')


class HIDBSL5Target(HIDBSL5, msp430.target.Target):
    """Combine the HID BSL5 backend and the common target code."""

    def __init__(self):
        msp430.target.Target.__init__(self)
        HIDBSL5.__init__(self)

    def add_extra_options(self):
        group = OptionGroup(self.parser, "Communication settings")

        group.add_option("-d", "--device",
                dest="device",
                help="hidraw device name",
                default=None)

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "BSL settings")

        group.add_option("--password",
                dest="password",
                action="store",
                help="transmit password before doing anything else, password is given in given (TI-Text/ihex/etc) file",
                default=None,
                metavar="FILE")

        self.parser.add_option_group(group)


    def close_connection(self):
        self.close()


    def open_connection(self):
        self.logger = logging.getLogger('BSL')
        if self.options.device is None: raise ValueError('device name required')
        self.open(self.options.device)

        # only fast mode supported by USB boot loader
        self.use_fast_mode = True
        self.buffer_size = 48

        if self.options.do_mass_erase:
            self.logger.info("Mass erase...")
            try:
                self.BSL_RX_PASSWORD('\xff'*30 + '\0'*2)
            except bsl5.BSL5Error:
                pass # it will fail - that is our intention to trigger the erase
            time.sleep(1)
            # after erase, unlock device
            self.BSL_RX_PASSWORD('\xff'*32)
            # remove mass_erase from action list so that it is not done
            # twice
            self.remove_action(self.mass_erase)
        else:
            if self.options.password is not None:
                password = msp430.memory.load(self.options.password).get_range(0xffe0, 0xffff)
                self.logger.info("Transmitting password: %s" % (password.encode('hex'),))
                self.BSL_RX_PASSWORD(password)

        # download full BSL
        self.logger.info("Download full BSL...")
        bsl_version_expected = (0x00, 0x05, 0x04, 0x34)
        full_bsl_txt = pkgutil.get_data('msp430.bsl5', 'RAM_BSL.00.05.04.34.txt')
        full_bsl = msp430.memory.load('BSL', StringIO(full_bsl_txt), format='titext')
        self.program_file(full_bsl)
        self.BSL_LOAD_PC(0x2504)

        # must re-initialize communication, BSL or USB system needs some time
        # to be ready
        self.logger.info("Waiting for BSL...")
        time.sleep(3)
        self.close()
        self.open(self.options.device)
        # checking version, this is also a connection check
        bsl_version = self.BSL_VERSION()
        if bsl_version_expected !=  bsl_version_expected:
            self.logger.error("BSL version mismatch (continuing anyway)")
        else:
            self.logger.debug("BSL version OK")

        #~ # Switch back to mode where we get ACKs
        #~ self.use_fast_mode = False


def main():
    # run the main application
    bsl_target = HIDBSL5Target()
    bsl_target.main()

if __name__ == '__main__':
    main()
