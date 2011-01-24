#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple MSP430 BSL5 implementation using the serial port.
"""

import sys
from msp430.bsl5 import bsl5
import serial
import struct
import logging
import time

from optparse import OptionGroup
import msp430.target
import msp430.memory


# interface specific commands
# UART
BSL_CHANGE_BAUD_RATE = 0x52    # Change baud rate

BSL_BAUD_RATE_D1 = {
    9600   : 0x02,
    19200  : 0x03,
    38400  : 0x04,
    57600  : 0x05,
    115200 : 0x06,
}

# possible answers
BSL5_UART_ERROR_CODES = {
        0x51: 'Header incorrect',
        0x52: 'Checksum incorrect',
        0x53: 'Packet size zero',
        0x54: 'Packet size exceeds buffer',
        0x55: 'Unknown error',
        0x56: 'Unknown baud rate',
}

BSL5_ACK = '\x00'


def crc_update(crc, byte):
    x = ((crc >> 8) ^ ord(byte)) & 0xff
    x ^= x >> 4
    return ((crc << 8) ^ (x << 12) ^ (x << 5) ^ x) & 0xffff


class SerialBSL5(bsl5.BSL5):
    """\
    Implementation of the BSL protocol over the serial port.
    """

    def __init__(self):
        bsl5.BSL5.__init__(self)
        self.serial = None
        self.logger = logging.getLogger('BSL')
        self.extra_timeout = None
        self.invertRST = False
        self.invertTEST = False
        self.swapResetTest = False
        self.testOnTX = False
        self.blindWrite = False
        # delay after control line changes
        self.control_delay = 0.05


    def open(self, port=0, baudrate=9600, ignore_answer=False):
        self.ignore_answer = ignore_answer
        self.logger.info('Opening serial port %r' % port)
        try:
            self.serial = serial.serial_for_url(
                port,
                baudrate=baudrate,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
        except AttributeError:  # old pySerial versions do not have serial_for_url
            self.serial = serial.Serial(
                port,
                baudrate=baudrate,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )


    def __del__(self):
        self.close()


    def close(self):
        """Close serial port"""
        if self.serial is not None:
            self.logger.info('closing serial port')
            self.serial.close()
            self.serial = None

    # interface specific commands

    def BSL_CHANGE_BAUD_RATE(self, multiply):
        packet = struct.pack('<B', multiply)
        answer = self.bsl(BSL_CHANGE_BAUD_RATE, packet, expect=0)
        self.check_answer(answer)


    def bsl(self, cmd, message='', expect=None):
        """\
        Low level access to the serial communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer. In case of a failure read timeout or rejected commands by
        the slave, it will raise an exception.

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, the answer is just returned.

        Frame format:
        +-----+----+----+-----------+----+----+
        | HDR | LL | LH | D1 ... DN | CL | CH |
        +-----+----+----+-----------+----+----+
        """
        # first synchronize with slave
        self.logger.debug('Command 0x%02x %s' % (cmd, message.encode('hex')))
        # prepare command with checksum
        txdata = struct.pack('<BHB', 0x80, 1+len(message), cmd) + message
        txdata += struct.pack('<H', reduce(crc_update, txdata, 0xffff))   # append checksum
        #~ self.logger.debug('Sending command: %r' % (txdata.encode('hex'),))
        # transmit command
        self.serial.write(txdata)
        # wait for command answer
        if self.blindWrite:
            time.sleep(0.100)
            return
        if self.ignore_answer:
            return

        self.logger.debug('Reading answer...')
        if self.extra_timeout is None:
            ans = self.serial.read(1)
        else:
            for timeout in range(self.extra_timeout):
                ans = self.serial.read(1)
                if ans:
                    break
        if ans != BSL5_ACK:
            if ans: raise bsl5.BSL5Error('BSL reports error: %s' % BSL5_UART_ERROR_CODES.get(ans, 'unknown error'))
            raise bsl5.BSL5Error('No ACK received (timeout)')

        head = self.serial.read(3)
        if len(head) != 3: raise bsl5.BSL5Timeout('timeout while reading answer (header)')
        pi, length = struct.unpack("<BH", head)
        if pi == '\x80':
            data = self.serial.read(length)
            if len(data) != length: raise bsl5.BSL5Timeout('timeout while reading answer (data)')
            crc_str = self.serial.read(2)
            if len(crc_str) != 2: raise bsl5.BSL5Timeout('timeout while reading answer (CRC)')
            crc = struct.unpack("<H", crc_str)
            crc_expected = reduce(crc_update, head + data, 0xffff)
            if crc != crc_expected:
                raise bsl5.BSLException('CRC error in answer')
            if expect is not None and length != expect:
                raise bsl5.BSL5Error('expected %d bytes, got %d bytes' % (expect, len(data)))
            return data
        else:
            if pi: raise bsl5.BSL5Error('received bad PI, expected 0x80 (got 0x%02x)' % (ord(pi),))
            raise bsl5.BSL5Error('received bad PI, expected 0x80 (got empty response)')


    def set_RST(self, level=True):
        """\
        Controls RST/NMI pin (0: GND; 1: VCC; unless inverted flag is set)
        """
        # invert signal if configured
        if self.invertRST:
            level = not level
        # set pin level
        if self.swapResetTest:
            self.serial.setRTS(level)
        else:
            self.serial.setDTR(level)
        time.sleep(self.control_delay)


    def set_TEST(self, level=True):
        """\
        Controls TEST pin (inverted on board: 0: VCC; 1: GND; unless inverted
        flag is set)
        """
        # invert signal if configured
        if self.invertTEST:
            level = not level
        # make TEST signal on TX pin, using break condition.
        if self.testOnTX:
            self.serial.setBreak(level)
        else:
            # set pin level
            if self.swapResetTest:
                self.serial.setDTR(level)
            else:
                self.serial.setRTS(level)
        time.sleep(self.control_delay)


    def set_baudrate(self, baudrate):
        """\
        Change the BSL baud rate on the target and switch the serial port.
        """
        self.logger.info('changing baud rate to %s' % (baudrate,))
        try:
            multiply = BSL_BAUD_RATE_D1[baudrate]
        except:
            raise ValueError('unsupported baud rate %s' % (baudrate,))
        else:
            self.BSL_CHANGE_BAUD_RATE(multiply)
            time.sleep(0.010)
            self.serial.baudrate = baudrate


    def start_bsl(self):
        """\
        Start the ROM-BSL using the pulse pattern on TEST and RST.
        """
        self.logger.info('ROM-BSL start pulse pattern')
        self.set_RST(True)      # power supply
        self.set_TEST(True)     # power supply
        time.sleep(0.250)       # charge capacitor on boot loader hardware

        self.set_RST(False)     # RST  pin: GND
        self.set_TEST(True)     # TEST pin: GND
        self.set_TEST(False)    # TEST pin: Vcc
        self.set_TEST(True)     # TEST pin: GND
        self.set_TEST(False)    # TEST pin: Vcc
        self.set_RST(True)      # RST  pin: Vcc
        self.set_TEST(True)     # TEST pin: GND
        time.sleep(0.250)       # give MSP430's oscillator time to stabilize

        self.serial.flushInput()    # clear buffers


class SerialBSL5Target(SerialBSL5, msp430.target.Target):
    """Combine the serial BSL backend and the common target code."""

    def __init__(self):
        msp430.target.Target.__init__(self)
        SerialBSL5.__init__(self)
        self.patch_in_use = False

    def add_extra_options(self):
        group = OptionGroup(self.parser, "Communication settings")

        group.add_option("-p", "--port",
                dest="port",
                help="Use com-port",
                default=0)
        group.add_option("--invert-test",
                dest="invert_test",
                action="store_true",
                help="invert RTS line",
                default=False)
        group.add_option("--invert-reset",
                dest="invert_reset",
                action="store_true",
                help="invert DTR line",
                default=False)
        group.add_option("--swap-reset-test",
                dest="swap_reset_test",
                action="store_true",
                help="exchenage RST and TEST signals (DTR/RTS)",
                default=False)
        group.add_option("--test-on-tx",
                dest="test_on_tx",
                action="store_true",
                help="TEST/TCK signal is muxed on TX line",
                default=False)

        self.parser.add_option_group(group)

        group = OptionGroup(self.parser, "BSL settings")

        group.add_option("--no-start",
                dest="start_pattern",
                action="store_false",
                help="no not use ROM-BSL start pattern on RST+TEST/TCK",
                default=True)

        group.add_option("-s", "--speed",
                dest="speed",
                type=int,
                help="change baud rate (default 9600)",
                default=None)

        group.add_option("--password",
                dest="password",
                action="store",
                help="transmit password before doing anything else, password is given in given (TI-Text/ihex/etc) file",
                default=None,
                metavar="FILE")

        group.add_option("--ignore-answer",
                dest="ignore_answer",
                action="store_true",
                help="do not wait for answer to BSL commands",
                default=False)

        group.add_option("--control-delay",
                dest="control_delay",
                type="float",
                help="set delay in seconds (float) for BSL start pattern",
                default=0.01)

        self.parser.add_option_group(group)


    def parse_extra_options(self):
        if self.verbose > 1:   # debug infos
            if hasattr(serial, 'VERSION'):
                sys.stderr.write("pySerial version: %s\n" % serial.VERSION)


    def close_connection(self):
        self.close()


    def open_connection(self):
        self.logger = logging.getLogger('BSL')
        self.open(
            self.options.port,
            ignore_answer = self.options.ignore_answer,
        )
        self.control_delay = self.options.control_delay

        if self.options.test_on_tx:
            self.testOnTX = True

        if self.options.invert_test:
            self.invertTEST = True

        if self.options.invert_reset:
            self.invertRST = True

        if self.options.swap_reset_test:
            self.swapResetTest = True

        self.set_TEST(True)
        self.set_RST(True)

        if self.options.start_pattern:
            self.start_bsl()


        if self.options.do_mass_erase:
            self.logger.info("Mass erase...")
            try:
                self.BSL_RX_PASSWORD('\xff'*30 + '\0'*2)
            except bsl5.BSL5Error:
                pass # it will fail - that is our intention to trigger the erase
            time.sleep(1)
            #~ self.extra_timeout = 6
            #~ self.mass_erase()
            #~ self.extra_timeout = None
            self.BSL_RX_PASSWORD('\xff'*32)
            # remove mass_erase from action list so that it is not done
            # twice
            self.remove_action(self.mass_erase)
        else:
            if self.options.password is not None:
                password = msp430.memory.load(self.options.password).get_range(0xffe0, 0xffff)
                self.logger.info("Transmitting password: %s" % (password.encode('hex'),))
                self.BSL_RX_PASSWORD(password)

        if self.options.speed is not None:
            try:
                self.set_baudrate(self.options.speed)
            except bsl5.BSLError:
                raise bsl5.BSLError("--speed option not supported by BSL on target")

        # configure the buffer
        #~ self.detect_buffer_size()


    # override reset method: use control line
    def reset(self):
        #~ time.sleep(0.25)
        #~ self.set_RST(True)      # power supply
        #~ self.set_TEST(True)     # power supply
        #~ time.sleep(0.1)
        #~ self.patch_in_use = False
        self.set_RST(False)
        #~ time.sleep(0.5)
        #~ SerialBSL.reset(self)
        #~ self.set_RST(True)
        #~ time.sleep(0.250)       # give MSP430's oscillator time to stabilize


def main():
    # run the main application
    bsl_target = SerialBSL5Target()
    bsl_target.main()

if __name__ == '__main__':
    main()
