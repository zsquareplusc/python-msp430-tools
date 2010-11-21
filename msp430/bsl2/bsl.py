"""
Simple MSP430 BSL implementation. The BSL class is abstract, i.e. it
requires that a bsl() function is implemented, by subbclassing it.

The bsl() function is responsible to implement the transport (e.g. serial
port access).
"""

import struct

#possible answers
BSL_SYNC         = '\x80'
CMD_FAILED       = '\x70'
DATA_FRAME       = '\x80'
DATA_ACK         = '\x90'
DATA_NAK         = '\xA0'

#commands for the MSP430 target
BSL_TXPWORD         = 0x10    # Receive password to unlock commands
BSL_TXBLK           = 0x12    # Transmit block to boot loader
BSL_RXBLK           = 0x14    # Receive  block from boot loader
BSL_ERASE           = 0x16    # Erase one segment
BSL_MERAS           = 0x18    # Erase complete FLASH memory
BSL_CHANGEBAUD      = 0x20    # Change baudrate
BSL_LOADPC          = 0x1A    # Load PC and start execution
BSL_ERASE_CHECK     = 0x1C    # Erase check of flash
BSL_TXVERSION       = 0x1E    # Get BSL version

class BSLException(Exception):
    """Errors from the slave"""

class BSLTimeout(BSLException):
    """got no answer from slave wthin time"""
    
class BSLError(BSLException):
    """command execution failed"""

class BSL:
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
        packet = struct.pack('<HH', address, length) + data
        answer = self.bsl(BSL_TXBLK, packet, expect = 0)

    def BSL_RXBLK(self, address, length):
        packet = struct.pack('<HH', address, length)
        answer = self.bsl(BSL_RXBLK, packet, expect=length)
        return answer

    def BSL_MERAS(self):
        packet = struct.pack('<HH', 0xfffe, 0xa506)
        answer = self.bsl(BSL_MERAS, packet, expect=0)
        
    def BSL_ERASE(self, address):
        packet = struct.pack('<HH', address, 0xa502)
        answer = self.bsl(BSL_ERASE, packet, expect=0)
        
    def BSL_CHANGEBAUD(self, bcsctl, multiply):
        packet = struct.pack('<HH', bcsctl, multiply)
        answer = self.bsl(BSL_CHANGEBAUD, packet, expect=0)
        
    def BSL_LOADPC(self, address):
        packet = struct.pack('<HH', address, 0)
        answer = self.bsl(BSL_LOADPC, packet, expect=0)

    def BSL_TXPWORD(self, password):
        packet = struct.pack('<HH', 0, 0) + password
        answer = self.bsl(BSL_TXPWORD, packet, expect=0)

    def BSL_TXVERSION(self):
        answer = self.bsl(BSL_TXVERSION, "\0"*4)
        return answer

    def BSL_HARDWARE_INFO(self):
        answer = self.bsl(BSL_HARDWARE_INFO, "\0"*4)
        return answer
        
    def BSL_RESET(self):
        answer = self.bsl(BSL_RESET, "\0"*4, expect=0)

    # - - - - - - High level functions - - - - - -
    def memory_read(self, address, length):
        data = []
        while length:
            size = min(self.MAXSIZE, length)
            data.append(self.BSL_RXBLK(address, size))
            address += size
            length -= size
        return ''.join(data)

    def memory_write(self, address, data):
        while data:
            block, data = data[:self.MAXSIZE], data[self.MAXSIZE:]
            self.BSL_TXBLK(address, block)
            address += len(block)

    def mass_erase(self):
        return self.BSL_MERAS()
        
    def erase(self, address):
        return self.BSL_ERASE(address)

    def execute(self, address):
        return self.BSL_LOADPC(address)

    def password(self, password):
        return self.BSL_TXPWORD(password)

    def version(self):
        try:
            return self.BSL_TXVERSION()
        except BSLError:
            #if command is not supported, try a memory read instead
            return self.BSL_RXBLK(0x0ff0, 16)

    def reset(self):
        # try a write to the watchdog instead
        try:
            self.BSL_TXBLK(0x0120, "\x08\x5a")
        except BSLError:
            #we can't verify the success of the reset...
            pass
        return True


class DummyBSL(BSL):
    def bsl(self, cmd, message='', expect=None, bad_crc=False):
        txdata = struct.pack('<cBBB', DATA_FRAME, cmd, len(message), len(message)) + message
        txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   #append checksum
        print repr(txdata), len(txdata)
        print ''.join(['\\x%02x' % ord(x) for x in txdata])

if __name__ == '__main__':
    dummy = DummyBSL()
    dummy.BSL_TXPWORD("\xff"*32)
