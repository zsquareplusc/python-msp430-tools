#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple MSP430 BSL implementation. The BSL class is abstract, i.e. it
requires that a bsl() method is implemented, by subclassing it.

The bsl() method is responsible to implement the transport (e.g. serial
port access).
"""

import struct

# possible answers
BSL_SYNC         = '\x80'
CMD_FAILED       = '\x70'
DATA_FRAME       = '\x80'
DATA_ACK         = '\x90'
DATA_NAK         = '\xA0'

# commands for the MSP430 target
BSL_TXPWORD         = 0x10    # Receive password to unlock commands
BSL_TXBLK           = 0x12    # Transmit block to boot loader
BSL_RXBLK           = 0x14    # Receive  block from boot loader
BSL_ERASE           = 0x16    # Erase one segment
BSL_MERAS           = 0x18    # Erase complete FLASH memory
BSL_CHANGEBAUD      = 0x20    # Change baud rate
BSL_SETMEMOFFSET    = 0x21    # MemoryAddress = OffsetValue << 16 + Actual Address
BSL_LOADPC          = 0x1A    # Load PC and start execution
BSL_ERASE_CHECK     = 0x1C    # Erase check of flash
BSL_TXVERSION       = 0x1E    # Get BSL version


class BSLException(Exception):
    """Errors from the slave"""

class BSLTimeout(BSLException):
    """got no answer from slave within time"""

class BSLError(BSLException):
    """command execution failed"""


class BSL(object):
    MAXSIZE = 240

    def checksum(self, data):
        """calculate the 16 bit checksum over the given data"""
        if len(data) & 1:
            raise ValueError("can't build checksum over odd-length data")
        checksum = 0
        for i in range(0, len(data), 2):
            (w,) = struct.unpack("<H", data[i:i+2])
            checksum ^= w
        return checksum & 0xffff

    def BSL_TXBLK(self, address, data):
        #~ print "BSL_TXBLK(0x%02x, len=%r)" % (address, len(data))
        length = len(data)
        packet = struct.pack('<HH', address, length) + bytes(data)
        answer = self.bsl(BSL_TXBLK, packet, expect = 0)

    def BSL_RXBLK(self, address, length):
        packet = struct.pack('<HH', address, length)
        answer = self.bsl(BSL_RXBLK, packet, expect=length)
        return answer

    def BSL_MERAS(self):
        packet = struct.pack('<HH', 0xfffe, 0xa506)
        answer = self.bsl(BSL_MERAS, packet, expect=0)

    def BSL_ERASE(self, address, option=0xa502):
        packet = struct.pack('<HH', address, option)
        answer = self.bsl(BSL_ERASE, packet, expect=0)

    def BSL_CHANGEBAUD(self, bcsctl, multiply):
        packet = struct.pack('<HH', bcsctl, multiply)
        answer = self.bsl(BSL_CHANGEBAUD, packet, expect=0)

    def BSL_SETMEMOFFSET(self, address_hi_bits):
        packet = struct.pack('<HH', address_hi_bits, 0)
        answer = self.bsl(BSL_SETMEMOFFSET, packet, expect=0)

    def BSL_LOADPC(self, address):
        packet = struct.pack('<HH', address, 0)
        answer = self.bsl(BSL_LOADPC, packet, expect=0)

    def BSL_TXPWORD(self, password):
        packet = struct.pack('<HH', 0, 0) + password
        answer = self.bsl(BSL_TXPWORD, packet, expect=0)

    def BSL_TXVERSION(self):
        answer = self.bsl(BSL_TXVERSION, "\0"*4)
        return answer

    # - - - - - - High level functions - - - - - -

    def __init__(self):
        self.extended_address_mode = False
        self.main_erase_cycles = 12

    def check_extended(self):
        """Automatically determine if BSL_SETMEMOFFSET can be used"""
        self.device_id, self.bsl_version = struct.unpack(">H8xH4x", self.version())
        if self.bsl_version >= 0x0212:
            self.extended_address_mode = True

    def memory_read(self, address, length):
        """\
        Read from memory. It creates multiple BSL_RXBLK commands internally
        when the size is larger than the block size.
        """
        data = bytearray()
        odd = bool(length & 1)
        if odd:
            length += 1
        while length:
            size = min(self.MAXSIZE, length)
            if self.extended_address_mode:
                self.BSL_SETMEMOFFSET(address >> 16)
            data.extend(self.BSL_RXBLK(address & 0xffff, size))
            address += size
            length -= size
        if odd and data:
            data.pop()  # remove the additional byte w've added on upload
        return data

    def memory_write(self, address, data):
        """\
        Write to memory. It creates multiple BSL_TXBLK commands internally
        when the size is larger than the block size.
        """
        if len(data) & 1:
            data += '\xff'
            #~ self.log.warn('memory_write: Odd length data not supported, padded with 0xff')
        while data:
            block, data = data[:self.MAXSIZE], data[self.MAXSIZE:]
            if self.extended_address_mode:
                self.BSL_SETMEMOFFSET(address >> 16)
            self.BSL_TXBLK(address & 0xffff, block)
            address += len(block)

    def mass_erase(self):
        """Clear all Flash memory."""
        return self.BSL_MERAS()

    def erase(self, address):
        """Erase Flash segment containing the given address."""
        return self.BSL_ERASE(address)

    def main_erase(self):
        """Erase Flash segment containing the given address."""
        # must execute command multiple times to meet cumulative erase time
        # required, see slaa89d, pg. 8
        for i in range(self.main_erase_cycles):
            self.BSL_ERASE(0xff00, 0xa504)

    def execute(self, address):
        """Start executing code on the target"""
        return self.BSL_LOADPC(address)

    def password(self, password):
        """Transmit the BSL password"""
        return self.BSL_TXPWORD(password)

    def version(self):
        """\
        Get the BSL version. The 16 bytes of the ROM that contain chip and
        BSL info are returned.
        """
        try:
            return self.BSL_TXVERSION()
        except BSLError:
            # if command is not supported, try a memory read instead
            return self.BSL_RXBLK(0x0ff0, 16)

    def reset(self):
        """\
        Reset the device. BSL is exit.
        XXX currently only suitable for F1xx, F2xx and F4xx devices as the WDT
            module is used.
        """
        # try a write to the watchdog
        try:
            self.BSL_TXBLK(0x0120, "\x08\x5a")
        except BSLError:
            # we can't verify the success of the reset...
            pass


# ----- test code only below this line -----

class DummyBSL(BSL):
    """Test code: show what the BSL command would send"""
    def bsl(self, cmd, message='', expect=None, bad_crc=False):
        txdata = struct.pack('<cBBB', DATA_FRAME, cmd, len(message), len(message)) + message
        txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   # append checksum
        print repr(txdata), len(txdata)
        print ''.join(['\\x%02x' % ord(x) for x in txdata])

if __name__ == '__main__':
    dummy = DummyBSL()
    dummy.BSL_TXPWORD("\xff"*32)
