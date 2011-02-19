#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
Simple MSP430 F5xx BSL implementation. The BSL class is abstract, i.e. it
requires that a bsl() method is implemented, by subclassing it.

The bsl() method is responsible to implement the transport (e.g. serial
port access, USB HID).
"""

import struct

# commands for the MSP430 target
BSL_RX_DATA_BLOCK       = 0x10    # Write to boot loader
BSL_RX_DATA_BLOCK_FAST  = 0x1b    # Write to boot loader
BSL_RX_PASSWORD         = 0x11    # Receive password to unlock commands
BSL_ERASE_SEGMENT       = 0x12    # Erase one segment
BSL_LOCK_INFO           = 0x13    # Toggle INFO_A lock bit
BSL_MASS_ERASE          = 0x15    # Erase complete FLASH memory
BSL_CRC_CHECK           = 0x16    # Run 16 bit CRC check over given area
BSL_LOAD_PC             = 0x17    # Load PC and start execution
BSL_TX_DATA_BLOCK       = 0x18    # Read from boot loader
BSL_VERSION             = 0x19    # Get BSL version
BSL_BUFFER_SIZE         = 0x1a    # Get BSL buffer size


class BSL5Exception(Exception):
    """Errors from the slave"""

class BSL5Timeout(BSL5Exception):
    """got no answer from slave within time"""

class BSL5Error(BSL5Exception):
    """command execution failed"""

BSL5_ERROR_CODES = {
        0x00: 'Operation successful',
        0x01: 'Flash write check failed',
        0x02: 'Flash fail bit set',
        0x03: 'Voltage change during program',
        0x04: 'BSL locked',
        0x05: 'BSL password error',
        0x06: 'Byte write forbidden',
        0x07: 'Unknown command',
        0x08: 'Packet length exceeds buffer size',
}


def three_bytes(address):
    """Convert a 24 bit address to a string with 3 bytes"""
    return '%c%c%c' % ((address & 0xff), (address >> 8) & 0xff, (address >> 16) & 0xff)


class BSL5(object):
    """\
    This class implements the core commands of a F5xx BSL.
    """

    def check_answer(self, data):
        if data[0] == '\x3b':
            if data[1] == '\0':
                return # SUCCESS!
            raise BSL5Error(BSL5_ERROR_CODES.get(ord(data[1]), 'unknown error response 0x%02x' % ord(data[1])))
        elif data[0] != '\x3a':
            raise BSL5Error('unknown response 0x%02x' % ord(data[0]))

    def BSL_RX_DATA_BLOCK(self, address, data):
        packet = three_bytes(address) + data
        answer = self.bsl(BSL_RX_DATA_BLOCK, packet, expect=0)
        self.check_answer(answer)

    def BSL_RX_DATA_BLOCK_FAST(self, address, data):
        packet = three_bytes(address) + data
        self.bsl(BSL_RX_DATA_BLOCK_FAST, packet, receive_response=False)

    def BSL_TX_DATA_BLOCK(self, address, length):
        packet = struct.pack('<3sH', three_bytes(address), length)
        answer = self.bsl(BSL_TX_DATA_BLOCK, packet, expect=length)
        self.check_answer(answer)
        return answer[1:]

    def BSL_MASS_ERASE(self):
        answer = self.bsl(BSL_MASS_ERASE, expect=0)
        self.check_answer(answer)

    def BSL_ERASE_SEGMENT(self, address):
        answer = self.bsl(BSL_ERASE_SEGMENT, three_bytes(address), expect=0)
        self.check_answer(answer)

    def BSL_LOAD_PC(self, address):
        self.bsl(BSL_LOAD_PC, three_bytes(address), receive_response=False)

    def BSL_RX_PASSWORD(self, password):
        answer = self.bsl(BSL_RX_PASSWORD, password, expect=0)
        self.check_answer(answer)

    def BSL_VERSION(self):
        """\
        Returns a tuple with
        - BSL vendor information
        - Command interpreter version
        - API version
        - Peripheral interface version
        """
        answer = self.bsl(BSL_VERSION, expect=4)
        self.check_answer(answer)
        return struct.unpack('<BBBBB', answer)[1:]

    def BSL_BUFFER_SIZE(self):
        answer = self.bsl(BSL_BUFFER_SIZE, expect=2)
        self.check_answer(answer)
        return struct.unpack('<BH', answer)[1]

    def BSL_LOCK_INFO(self):
        answer = self.bsl(BSL_LOCK_INFO, expect=0)
        self.check_answer(answer)

    def BSL_CRC_CHECK(self):
        answer = self.bsl(BSL_CRC_CHECK, expect=0)
        self.check_answer(answer)
        return struct.unpack('<BH', answer)[1]

    # - - - - - - High level functions - - - - - -
    def detect_buffer_size(self):
        """Auto detect buffer size"""
        try:
            self.buffer_size = self.BSL_BUFFER_SIZE()
        except BSL5Error:
            pass

    def __init__(self):
        self.buffer_size = 240
        self.use_fast_mode = False

    def memory_read(self, address, length):
        """\
        Read from memory. It creates multiple BSL_TX_DATA_BLOCK commands
        internally when the size is larger than the block size.
        """
        if self.buffer_size is None: raise BSL5Error('block size!?')
        data = bytearray()
        odd = bool(length & 1)
        if odd:
            length += 1
        while length:
            size = min(self.buffer_size, length)
            data.extend(bytes(self.BSL_TX_DATA_BLOCK(address, size)))
            address += size
            length -= size
        if odd and data:
            data.pop()  # remove the additional byte w've added on upload
        return data

    def memory_write(self, address, data):
        """\
        Write to memory. It creates multiple BSL_RX_DATA_BLOCK or
        BSL_RX_DATA_BLOCK_FAST commands internally when the size is larger than
        the block size.
        """
        if self.buffer_size is None: raise BSL5Error('block size!?')
        if len(data) & 1:
            data += '\xff'
            #~ self.log.warn('memory_write: Odd length data not supported, padded with 0xff')
        while data:
            block, data = data[:self.buffer_size], data[self.buffer_size:]
            if self.use_fast_mode:
                self.BSL_RX_DATA_BLOCK_FAST(address, block)
            else:
                self.BSL_RX_DATA_BLOCK(address, block)
            address += len(block)

    def mass_erase(self):
        """Clear all Flash memory."""
        return self.BSL_MASS_ERASE()

    def erase(self, address):
        """Erase Flash segment containing the given address."""
        return self.BSL_ERASE_SEGMENT(address)

    #~ def main_erase(self):
        #~ """Erase Flash segment containing the given address."""
        #~ # must execute command multiple times to meet cumulative erase time
        #~ # required, see slaa89d, pg. 8
        #~ self.BSL_ERASE(0xff00, 0xa504)

    def execute(self, address):
        """Start executing code on the target"""
        return self.BSL_LOAD_PC(address)

    def password(self, password):
        """Transmit the BSL password"""
        return self.BSL_RX_PASSWORD(password)

    def version(self):
        """\
        Get the BSL version. The 16 bytes of the ROM that contain chip and
        BSL info are returned.
        """
        return self.BSL_VERSION()

    def reset(self):
        """\
        Reset the device. BSL is exit.
        XXX currently only suitable for F5xx devices as the WDT module is used.
        """
        # try a write to the watchdog
        try:
            self.BSL_RX_DATA_BLOCK_FAST(0x015c, "\x00\x00")  # XXX set a delay instead of immediate reset
        except BSL5Error:
            # we can't verify the success of the reset...
            pass


# ----- test code only below this line -----

if __name__ == '__main__':
    class DummyBSL(BSL5):
        """Test code: show what the BSL command would send"""
        def bsl(self, cmd, message='', expect=None):
            txdata = struct.pack('<cBBB', DATA_FRAME, cmd, len(message), len(message)) + message
            txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   #append checksum
            print repr(txdata), len(txdata)
            print ''.join(['\\x%02x' % ord(x) for x in txdata])

    dummy = DummyBSL()
    dummy.BSL_RX_PASSWORD("\xff"*32)
