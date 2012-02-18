#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple MSP430 BSL implementation using the serial port.
"""

import sys
from msp430.bsl import bsl
import serial
import struct
import logging
import time
import pkgutil
from cStringIO import StringIO

from optparse import OptionGroup
import msp430.target
import msp430.memory


F1x_baudrate_args = {
     9600:[0x8580, 0x0000],
    19200:[0x86e0, 0x0001],
    38400:[0x87e0, 0x0002],
    57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
}
F2x_baudrate_args = {
     9600:[0x8880, 0x0000],
    19200:[0x8b00, 0x0001],
    38400:[0x8c80, 0x0002],
}
F4x_baudrate_args = {
     9600:[0x9800, 0x0000],
    19200:[0xb000, 0x0001],
    38400:[0xc800, 0x0002],
    57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
}


class SerialBSL(bsl.BSL):
    """\
    Implementation of the BSL protocol over the serial port.
    """

    def __init__(self):
        bsl.BSL.__init__(self)
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
                stopbits=serial.STOPBITS_TWO,
                timeout=1,
            )
        except AttributeError:  # old pySerial versions do not have serial_for_url
            self.serial = serial.Serial(
                port,
                baudrate=baudrate,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_TWO,
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


    def sync(self):
        """\
        Send the sync character and wait for an acknowledge.
        The sync procedure is retried if it fails once or twice.
        """
        self.logger.debug('Sync...')
        if self.blindWrite:
            self.serial.write(bsl.BSL_SYNC)
            time.sleep(0.030)
        else:
            for tries in '210':
                self.serial.flushInput()
                self.serial.write(bsl.BSL_SYNC)
                ack = self.serial.read(1)
                if ack == bsl.DATA_ACK:
                    self.logger.debug('Sync OK')
                    return
                else:
                    if tries != '0':
                        self.logger.debug('Sync failed, retry...')
                    # if something was received, ensure that a small delay is made
                    if ack:
                        time.sleep(0.2)
            self.logger.error('Sync failed, aborting...')
            raise bsl.BSLTimeout('could not sync')


    def bsl(self, cmd, message='', expect=None):
        """\
        Low level access to the serial communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer (an empty string for simple DATA_ACKs). In case of a failure
        read timeout or rejected commands by the slave, it will raise an
        exception.

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, DATA_ACK and DATA_FRAME are accepted and the
        answer is just returned.

        Frame format:
        +-----+-----+----+----+-----------+----+----+
        | HDR | CMD | L1 | L2 | D1 ... DN | CL | CH |
        +-----+-----+----+----+-----------+----+----+
        """
        # first synchronize with slave
        self.sync()
        self.logger.debug('Command 0x%02x %s' % (cmd, message.encode('hex')))
        # prepare command with checksum
        txdata = struct.pack('<cBBB', bsl.DATA_FRAME, cmd, len(message), len(message)) + message
        txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   #append checksum
        #~ self.logger.debug('Sending command: %r' % (txdata,))
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
        # depending on answer type, read more, raise exceptions etc.
        if ans == '':
            raise bsl.BSLTimeout('timeout while reading answer (ack)')
        elif ans == bsl.DATA_NAK:
            self.logger.debug('Command failed (DATA_NAK)')
            raise bsl.BSLError('command failed (DATA_NAK)')
        elif ans == bsl.CMD_FAILED:
            self.logger.debug('Command failed (CMD_FAILED)')
            raise bsl.BSLError('command failed (CMD_FAILED)')
        elif ans == bsl.DATA_ACK:
            self.logger.debug('Simple ACK')
            if expect is not None and expect > 0:
                raise bsl.BSLError('expected data, but received a simple ACK')
            return ''
        elif ans == bsl.DATA_FRAME:
            self.logger.debug('Data frame...')
            head = self.serial.read(3)
            if len(head) != 3:
                raise bsl.BSLTimeout('timeout while reading answer (header)')
            (self.dummy, l1, l2) = struct.unpack('<BBB', head)
            if l1 != l2:
                raise bsl.BSLError('broken answer (L1 != L2)')
            if l1:
                data = self.serial.read(l1)
                if len(data) != l1:
                    raise bsl.BSLTimeout('timeout while reading answer (data)')
            else:
                data = ''
            checksum = self.serial.read(2)
            if len(checksum) != 2:
                raise bsl.BSLTimeout('timeout while reading answer (checksum)')
            if self.checksum(ans + head + data) ^ 0xffff == struct.unpack("<H", checksum)[0]:
                if expect is not None and len(data) != expect:
                    raise bsl.BSLError('expected %d bytes, got %d bytes' % (expect, len(data)))
                self.logger.debug('Data frame: %s' % data.encode('hex'))
                return data
            else:
                raise bsl.BSLError('checksum error in answer')
        else:
            self.logger.debug('unexpected answer %r' % (ans,))
            raise bsl.BSLError('unexpected answer: %r' % (ans,))


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
        family = msp430.target.identify_device(self.device_id, self.bsl_version)
        if family == msp430.target.F1x:
            table = F1x_baudrate_args
        elif family == msp430.target.F2x:
            table = F2x_baudrate_args
        elif family == msp430.target.F4x:
            table = F4x_baudrate_args
        else:
            raise BSLError('No baud rate table for %s' % (family,))
        self.logger.info('changing baud rate to %s' % (baudrate,))
        try:
            a, l = table[baudrate]
        except:
            raise ValueError('unsupported baud rate %s' % (baudrate,))
        else:
            self.BSL_CHANGEBAUD(a, l)
            time.sleep(0.010)   # recommended delay
            self.serial.baudrate = baudrate


    def start_bsl(self):
        """\
        Start the ROM-BSL using the pulse pattern on TEST and RST.
        """
        self.logger.info('ROM-BSL start pulse pattern')
        self.set_RST(True)      # power supply
        self.set_TEST(True)     # power supply
        #~ time.sleep(0.250)       # charge capacitor on boot loader hardware
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


class SerialBSLTarget(SerialBSL, msp430.target.Target):
    """Combine the serial BSL backend and the common target code."""

    def __init__(self):
        msp430.target.Target.__init__(self)
        SerialBSL.__init__(self)
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
                help="exchange RST and TEST signals (DTR/RTS)",
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

        group.add_option("--replace-bsl",
                dest="replace_bsl",
                action="store_true",
                help="download replacement BSL (V1.50) for F1x and F4x devices with 2k RAM",
                default=False)

        group.add_option("--erase-cycles",
                dest="extra_erase_cycles",
                type="int",
                help="configure extra erase cycles (e.g. very old F149 chips require this for --main-erase)",
                default=None)
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

        if self.options.extra_erase_cycles is not None:
            self.main_erase_cycles += self.options.extra_erase_cycles

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
            self.extra_timeout = 6
            self.mass_erase()
            self.extra_timeout = None
            self.BSL_TXPWORD('\xff'*32)
            # remove mass_erase from action list so that it is not done
            # twice
            self.remove_action(self.mass_erase)
        else:
            if self.options.password is not None:
                password = msp430.memory.load(self.options.password).get_range(0xffe0, 0xffff)
                self.logger.info("Transmitting password: %s" % (password.encode('hex'),))
                self.BSL_TXPWORD(password)

        # check for extended features (e.g. >64kB support)
        self.logger.debug('Checking if device has extended features')
        self.check_extended()

        if self.options.replace_bsl:
            family = msp430.target.identify_device(self.device_id, self.bsl_version)
            if family == msp430.target.F1x:
                bsl_name = 'BL_150S_14x.txt'
                #~ bsl_name = 'BS_150S_14x.txt'
            elif family == msp430.target.F4x:
                bsl_name = 'BL_150S_44x.txt'
            else:
                raise BSLError('No replacement BSL for %s' % (family,))

            self.logger.info('Download replacement BSL as requested by --replace-bsl')
            replacement_bsl_txt = pkgutil.get_data('msp430.bsl', bsl_name)
            replacement_bsl = msp430.memory.load('BSL', StringIO(replacement_bsl_txt), format='titext')
            self.program_file(replacement_bsl)

            bsl_start_address = struct.unpack("<H", replacement_bsl.get(0x0220, 2))[0]
            self.execute(bsl_start_address)
            self.logger.info("Starting new BSL at 0x%04x" % (bsl_start_address,))
            time.sleep(0.050)   # give BSL some time to initialize
            #~ if self.options.password is not None:
                #~ self.BSL_TXPWORD(password)
        else:
            if self.bsl_version <= 0x0110:
                self.logger.info('Buggy BSL, applying patch')
                patch_txt = pkgutil.get_data('msp430.bsl', 'patch.txt')
                patch = msp430.memory.load('PATCH', StringIO(patch_txt), format='titext')
                self.program_file(patch)
                self.patch_in_use = True

        if self.options.speed is not None:
            try:
                self.set_baudrate(self.options.speed)
            except bsl.BSLError:
                raise bsl.BSLError("--speed option not supported by BSL on target")

    # special versions of TX and RX block functions are needed in order to
    # apply the patch on buggy devices

    def BSL_TXBLK(self, address, data):
        if self.patch_in_use:
            self.logger.debug("activate patch")
            self.BSL_LOADPC(0x0220)
        return SerialBSL.BSL_TXBLK(self, address, data)

    def BSL_RXBLK(self, address, length):
        if self.patch_in_use:
            self.logger.debug("activate patch")
            self.BSL_LOADPC(0x0220)
        return SerialBSL.BSL_RXBLK(self, address, length)


    # override reset method: use control line
    def reset(self):
        """Reset the device."""
        
        self.logger.info('Reset device')
        
        #~ time.sleep(0.25)
        #~ self.set_RST(True)      # power supply
        #~ self.set_TEST(True)     # power supply
        #~ time.sleep(0.1)
        #~ self.patch_in_use = False
        self.set_RST(False)
        time.sleep(0.1)
        #~ SerialBSL.reset(self)
        self.set_RST(True)
        #~ time.sleep(0.250)       # give MSP430's oscillator time to stabilize


def main():
    # run the main application
    bsl_target = SerialBSLTarget()
    bsl_target.main()
