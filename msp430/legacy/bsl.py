#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2001-2010 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)
#
# fixes from Colin Domoney
#
# based on the application note slas96b.pdf from Texas Instruments, Inc.,
# Volker Rzehak
# additional infos from slaa089a.pdf

import sys, time, string, cStringIO, struct
import serial
from msp430.memory import Memory

DEBUG = 0

# copy of the patch file provided by TI
# this part is (C) by Texas Instruments
PATCH = """@0220
31 40 1A 02 09 43 B0 12 2A 0E B0 12 BA 0D 55 42
0B 02 75 90 12 00 1F 24 B0 12 BA 02 55 42 0B 02
75 90 16 00 16 24 75 90 14 00 11 24 B0 12 84 0E
06 3C B0 12 94 0E 03 3C 21 53 B0 12 8C 0E B2 40
10 A5 2C 01 B2 40 00 A5 28 01 30 40 42 0C 30 40
76 0D 30 40 AC 0C 16 42 0E 02 17 42 10 02 E2 B2
08 02 14 24 B0 12 10 0F 36 90 00 10 06 28 B2 40
00 A5 2C 01 B2 40 40 A5 28 01 D6 42 06 02 00 00
16 53 17 83 EF 23 B0 12 BA 02 D3 3F B0 12 10 0F
17 83 FC 23 B0 12 BA 02 D0 3F 18 42 12 02 B0 12
10 0F D2 42 06 02 12 02 B0 12 10 0F D2 42 06 02
13 02 38 E3 18 92 12 02 BF 23 E2 B3 08 02 BC 23
30 41
q
"""

# These BSL's are (C) by TI. They come with the application note slaa089a
F1X_BSL = """@0220
24 02 2E 02 31 40 20 02 2B D2 C0 43 EA FF 32 C2
F2 C0 32 00 00 00 B2 40 80 5A 20 01 F2 40 85 00
57 00 F2 40 80 00 56 00 E2 D3 21 00 E2 D3 22 00
E2 C3 26 00 E2 C2 2A 00 E2 C2 2E 00 B2 40 10 A5
2C 01 B2 40 00 A5 28 01 3B C0 3A 00 B0 12 D6 04
82 43 12 02 09 43 36 40 0A 02 37 42 B0 12 AC 05
C6 4C 00 00 16 53 17 83 F9 23 D2 92 0C 02 0D 02
28 20 55 42 0B 02 75 90 12 00 80 24 75 90 10 00
6D 24 B0 12 9C 04 55 42 0B 02 75 90 18 00 31 24
75 90 1E 00 B8 24 75 90 20 00 17 24 2B B2 11 24
75 90 16 00 22 24 75 90 14 00 B3 24 75 90 1A 00
18 24 75 90 1C 00 45 24 04 3C B0 12 36 05 BE 3F
21 53 B0 12 3C 05 BA 3F 03 43 B0 12 36 05 D2 42
0E 02 56 00 D2 42 0F 02 57 00 D2 42 10 02 16 02
AD 3F B0 12 36 05 10 42 0E 02 16 42 0E 02 15 43
07 3C 36 40 FE FF B2 40 06 A5 10 02 35 40 0C 00
B2 40 00 A5 2C 01 92 42 10 02 28 01 B6 43 00 00
92 B3 2C 01 FD 23 15 83 F3 23 36 90 FE FF CD 27
37 40 80 00 36 F0 80 FF 36 90 00 11 0E 28 07 57
36 F0 00 FF 36 90 00 12 08 28 07 57 36 F0 00 FE
04 3C 16 42 0E 02 17 42 10 02 35 43 75 96 03 20
17 83 FC 23 B2 3F 82 46 00 02 B3 3F 36 40 E0 FF
37 40 20 00 B0 12 AC 05 7C 96 01 24 2B D3 17 83
F9 23 2B C2 B0 12 9C 04 2B D2 9F 3F 16 42 0E 02
17 42 10 02 2B B2 38 24 3B D0 10 00 B0 12 AC 05
36 90 00 10 06 2C 36 90 00 01 09 2C C6 4C 00 00
25 3C B2 40 00 A5 2C 01 B2 40 40 A5 28 01 16 B3
03 20 C2 4C 14 02 1A 3C C2 4C 15 02 86 9A FD FF
08 24 2B D3 3B B0 20 00 04 20 3B D0 20 00 82 46
00 02 36 90 01 02 04 28 3B D2 3B B0 10 00 02 24
3B C0 32 00 1A 42 14 02 86 4A FF FF 16 53 17 83
CD 23 B0 12 9C 04 61 3F B0 12 AC 05 17 83 FC 23
B0 12 9C 04 5E 3F B2 40 F0 0F 0E 02 B2 40 10 00
10 02 B2 40 80 00 0A 02 D2 42 10 02 0C 02 D2 42
10 02 0D 02 82 43 12 02 09 43 36 40 0A 02 27 42
7C 46 B0 12 40 05 17 83 FB 23 16 42 0E 02 17 42
10 02 36 90 00 01 0A 28 B2 46 14 02 5C 42 14 02
B0 12 40 05 17 83 5C 42 15 02 01 3C 7C 46 B0 12
40 05 17 83 EE 23 B2 E3 12 02 5C 42 12 02 B0 12
40 05 5C 42 13 02 B0 12 40 05 E0 3E 18 42 12 02
B0 12 AC 05 C2 4C 12 02 B0 12 AC 05 C2 4C 13 02
38 E3 3B B2 0A 24 86 9A FE FF 07 24 3B B0 20 00
04 20 16 53 82 46 00 02 2B D3 18 92 12 02 08 23
2B B3 06 23 30 41 E2 B2 28 00 FD 27 E2 B2 28 00
FD 23 B2 40 24 02 60 01 E2 B2 28 00 FD 27 15 42
70 01 05 11 05 11 05 11 82 45 02 02 05 11 82 45
04 02 B2 80 1E 00 04 02 57 42 16 02 37 80 03 00
05 11 05 11 17 53 FD 23 35 50 40 A5 82 45 2A 01
35 42 B2 40 24 02 60 01 92 92 70 01 02 02 FC 2F
15 83 F7 23 09 43 7C 40 90 00 02 3C 7C 40 A0 00
C2 43 07 02 C9 EC 12 02 19 E3 1B C3 55 42 07 02
55 45 56 05 00 55 0C 2E 2E 2E 2E 2E 2E 2E 2E 1A
34 34 92 42 70 01 72 01 B2 50 0C 00 72 01 07 3C
1B B3 0B 20 82 43 62 01 92 B3 62 01 FD 27 E2 C3
21 00 0A 3C 4C 11 F6 2B 1B E3 82 43 62 01 92 B3
62 01 FD 27 E2 D3 21 00 92 52 02 02 72 01 D2 53
07 02 F0 90 0C 00 61 FC D1 23 30 41 C2 43 09 02
1B C3 55 42 09 02 55 45 BC 05 00 55 0C 56 56 56
56 56 56 56 56 36 76 00 E2 B2 28 00 FD 23 92 42
70 01 72 01 92 52 04 02 72 01 82 43 62 01 92 B3
62 01 FD 27 E2 B2 28 00 1E 28 2B D3 1C 3C 4C 10
1A 3C 82 43 62 01 92 B3 62 01 FD 27 E2 B2 28 00
01 28 1B E3 1B B3 01 24 2B D3 C9 EC 12 02 19 E3
0A 3C 82 43 62 01 92 B3 62 01 FD 27 E2 B2 28 00
E6 2B 4C 10 1B E3 92 52 02 02 72 01 D2 53 09 02
C0 3F 82 43 62 01 92 B3 62 01 FD 27 E2 B2 28 00
01 2C 2B D3 30 41
q
"""

F4X_BSL = """@0220
24 02 2E 02 31 40 20 02 2B D2 C0 43 EA FF 32 C2
F2 C0 32 00 00 00 B2 40 80 5A 20 01 32 D0 40 00
C2 43 50 00 F2 40 98 00 51 00 F2 C0 80 00 52 00
D2 D3 21 00 D2 D3 22 00 D2 C3 26 00 E2 C3 22 00
E2 C3 26 00 B2 40 10 A5 2C 01 B2 40 00 A5 28 01
3B C0 3A 00 B0 12 DE 04 82 43 12 02 09 43 36 40
0A 02 37 42 B0 12 B4 05 C6 4C 00 00 16 53 17 83
F9 23 D2 92 0C 02 0D 02 28 20 55 42 0B 02 75 90
12 00 80 24 75 90 10 00 6D 24 B0 12 A4 04 55 42
0B 02 75 90 18 00 31 24 75 90 1E 00 B8 24 75 90
20 00 17 24 2B B2 11 24 75 90 16 00 22 24 75 90
14 00 B3 24 75 90 1A 00 18 24 75 90 1C 00 45 24
04 3C B0 12 3E 05 BE 3F 21 53 B0 12 44 05 BA 3F
03 43 B0 12 3E 05 D2 42 0E 02 50 00 D2 42 0F 02
51 00 D2 42 10 02 16 02 AD 3F B0 12 3E 05 10 42
0E 02 16 42 0E 02 15 43 07 3C 36 40 FE FF B2 40
06 A5 10 02 35 40 0C 00 B2 40 00 A5 2C 01 92 42
10 02 28 01 B6 43 00 00 92 B3 2C 01 FD 23 15 83
F3 23 36 90 FE FF CD 27 37 40 80 00 36 F0 80 FF
36 90 00 11 0E 28 07 57 36 F0 00 FF 36 90 00 12
08 28 07 57 36 F0 00 FE 04 3C 16 42 0E 02 17 42
10 02 35 43 75 96 03 20 17 83 FC 23 B2 3F 82 46
00 02 B3 3F 36 40 E0 FF 37 40 20 00 B0 12 B4 05
7C 96 01 24 2B D3 17 83 F9 23 2B C2 B0 12 A4 04
2B D2 9F 3F 16 42 0E 02 17 42 10 02 2B B2 38 24
3B D0 10 00 B0 12 B4 05 36 90 00 10 06 2C 36 90
00 01 09 2C C6 4C 00 00 25 3C B2 40 00 A5 2C 01
B2 40 40 A5 28 01 16 B3 03 20 C2 4C 14 02 1A 3C
C2 4C 15 02 86 9A FD FF 08 24 2B D3 3B B0 20 00
04 20 3B D0 20 00 82 46 00 02 36 90 01 02 04 28
3B D2 3B B0 10 00 02 24 3B C0 32 00 1A 42 14 02
86 4A FF FF 16 53 17 83 CD 23 B0 12 A4 04 61 3F
B0 12 B4 05 17 83 FC 23 B0 12 A4 04 5E 3F B2 40
F0 0F 0E 02 B2 40 10 00 10 02 B2 40 80 00 0A 02
D2 42 10 02 0C 02 D2 42 10 02 0D 02 82 43 12 02
09 43 36 40 0A 02 27 42 7C 46 B0 12 48 05 17 83
FB 23 16 42 0E 02 17 42 10 02 36 90 00 01 0A 28
B2 46 14 02 5C 42 14 02 B0 12 48 05 17 83 5C 42
15 02 01 3C 7C 46 B0 12 48 05 17 83 EE 23 B2 E3
12 02 5C 42 12 02 B0 12 48 05 5C 42 13 02 B0 12
48 05 E0 3E 18 42 12 02 B0 12 B4 05 C2 4C 12 02
B0 12 B4 05 C2 4C 13 02 38 E3 3B B2 0A 24 86 9A
FE FF 07 24 3B B0 20 00 04 20 16 53 82 46 00 02
2B D3 18 92 12 02 08 23 2B B3 06 23 30 41 E2 B3
20 00 FD 27 E2 B3 20 00 FD 23 B2 40 24 02 60 01
E2 B3 20 00 FD 27 15 42 70 01 05 11 05 11 05 11
82 45 02 02 05 11 82 45 04 02 B2 80 1E 00 04 02
57 42 16 02 37 80 03 00 05 11 05 11 17 53 FD 23
35 50 40 A5 82 45 2A 01 35 42 B2 40 24 02 60 01
92 92 70 01 02 02 FC 2F 15 83 F7 23 09 43 7C 40
90 00 02 3C 7C 40 A0 00 C2 43 07 02 C9 EC 12 02
19 E3 1B C3 55 42 07 02 55 45 5E 05 00 55 0C 2E
2E 2E 2E 2E 2E 2E 2E 1A 34 34 92 42 70 01 72 01
B2 50 0C 00 72 01 07 3C 1B B3 0B 20 82 43 62 01
92 B3 62 01 FD 27 D2 C3 21 00 0A 3C 4C 11 F6 2B
1B E3 82 43 62 01 92 B3 62 01 FD 27 D2 D3 21 00
92 52 02 02 72 01 D2 53 07 02 F0 90 0C 00 59 FC
D1 23 30 41 C2 43 09 02 1B C3 55 42 09 02 55 45
C4 05 00 55 0C 56 56 56 56 56 56 56 56 36 76 00
E2 B3 20 00 FD 23 92 42 70 01 72 01 92 52 04 02
72 01 82 43 62 01 92 B3 62 01 FD 27 E2 B3 20 00
1E 28 2B D3 1C 3C 4C 10 1A 3C 82 43 62 01 92 B3
62 01 FD 27 E2 B3 20 00 01 28 1B E3 1B B3 01 24
2B D3 C9 EC 12 02 19 E3 0A 3C 82 43 62 01 92 B3
62 01 FD 27 E2 B3 20 00 E6 2B 4C 10 1B E3 92 52
02 02 72 01 D2 53 09 02 C0 3F 82 43 62 01 92 B3
62 01 FD 27 E2 B3 20 00 01 2C 2B D3 30 41
q
"""

# cpu types for "change baudrate"
# use strings as ID so that they can be used in outputs too
F1x                     = "F1x family"
F2x                     = "F2x family"
F4x                     = "F4x family"

# known device list
deviceids = {
    0x1132: F1x,
    0x1232: F1x,
    0xf112: F1x,
    0xf123: F1x,
    0xf149: F1x,
    0xf169: F1x,
    0xf16c: F1x,
    0xf413: F4x,
    0xf427: F4x,
    0xf439: F4x,
    0xf449: F4x,
    0xf26f: F2x,
}

class BSLException(Exception):
    pass

class LowLevel:
    "lowlevel communication"
    #Constants
    MODE_SSP                = 0
    MODE_BSL                = 1

    BSL_SYNC                = 0x80
    BSL_TXPWORD             = 0x10
    BSL_TXBLK               = 0x12 #Transmit block to boot loader
    BSL_RXBLK               = 0x14 #Receive  block from boot loader
    BSL_ERASE               = 0x16 #Erase one segment
    BSL_MERAS               = 0x18 #Erase complete FLASH memory
    BSL_CHANGEBAUD          = 0x20 #Change baudrate
    BSL_SETMEMOFFSET        = 0x21 #MemoryAddress = OffsetValue << 16 + Actual Address
    BSL_LOADPC              = 0x1A #Load PC and start execution
    BSL_TXVERSION           = 0x1E #Get BSL version

    # Upper limit of address range that might be modified by
    # "BSL checksum bug".
    BSL_CRITICAL_ADDR       = 0x0A00

    # Header Definitions
    CMD_FAILED              = 0x70
    DATA_FRAME              = 0x80
    DATA_ACK                = 0x90
    DATA_NAK                = 0xA0

    QUERY_POLL              = 0xB0
    QUERY_RESPONSE          = 0x50

    OPEN_CONNECTION         = 0xC0
    ACK_CONNECTION          = 0x40

    DEFAULT_TIMEOUT         =   1
    DEFAULT_PROLONG         =  10
    MAX_FRAME_SIZE          = 256
    MAX_DATA_BYTES          = 250
    MAX_DATA_WORDS          = 125

    MAX_FRAME_COUNT         = 16

    # Error messages
    ERR_COM                 = "Unspecific error"
    ERR_RX_NAK              = "NAK received (wrong password?)"
    # ERR_CMD_NOT_COMPLETED  = "Command did not send ACK: indicates that it didn't complete correctly"
    ERR_CMD_FAILED          = "Command failed, is not defined or is not allowed"
    ERR_BSL_SYNC            = "Bootstrap loader synchronization error"
    ERR_FRAME_NUMBER        = "Frame sequence number error."

    def calcChecksum(self, data, length):
        """Calculates a checksum of "data"."""
        checksum = 0

        for i in range(length/2):
            checksum = checksum ^ (ord(data[i*2]) | (ord(data[i*2+1]) << 8))    #xor-ing
        return 0xffff & (checksum ^ 0xffff)         # inverting

    def __init__(self, aTimeout = None, aProlongFactor = None):
        """init bsl object, don't connect yet"""
        if aTimeout is None:
            self.timeout = self.DEFAULT_TIMEOUT
        else:
            self.timeout = aTimeout
        if aProlongFactor is None:
            self.prolongFactor = self.DEFAULT_PROLONG
        else:
            self.prolongFactor = aProlongFactor

        # flags for inverted use of control pins
        # used for some hardware
        self.invertRST = 0
        self.invertTEST = 0
        self.swapResetTest = 0
        self.testOnTX = 0
        self.ignoreAnswer = 0

        self.protocolMode = self.MODE_BSL
        self.BSLMemAccessWarning = 0            # Default: no warning.
        self.slowmode = 0                       # give a little more time when changing the control lines
        self.memoffset = 0

    def comInit(self, port):
        """Tries to open the serial port given and
        initialises the port and variables.
        The timeout and the number of allowed errors is multiplied by
        'aProlongFactor' after transmission of a command to give
        plenty of time to the micro controller to finish the command.
        Returns zero if the function is successful."""
        if DEBUG > 1: sys.stderr.write("* comInit()\n")
        self.seqNo = 0
        self.reqNo = 0
        self.rxPtr = 0
        self.txPtr = 0
        # Startup-Baudrate: 9600,8,E,1, 1s timeout
        self.serialport = serial.Serial(
            port,
            9600,
            parity = serial.PARITY_EVEN,
            timeout = self.timeout
        )
        if DEBUG: sys.stderr.write("using serial port %r\n" % self.serialport.portstr)
        self.SetRSTpin()                        # enable power
        self.SetTESTpin()                       # enable power
        self.serialport.flushInput()
        self.serialport.flushOutput()

    def comDone(self):
        """Closes the used serial port.
        This function must be called at the end of a program,
        otherwise the serial port might not be released and can not be
        used in other programs.
        Returns zero if the function is successful."""
        if DEBUG > 1: sys.stderr.write("* comDone()")
        self.SetRSTpin(0)                       # disable power
        self.SetTESTpin(0)                      # disable power
        self.serialport.close()

    def comRxHeader(self):
        """receive header and split data"""
        if DEBUG > 1: sys.stderr.write("* comRxHeader()\n")

        hdr = self.serialport.read(1)
        if not hdr: raise BSLException("Timeout")
        rxHeader = ord(hdr) & 0xf0;
        rxNum    = ord(hdr) & 0x0f;

        if self.protocolMode == self.MODE_BSL:
            self.reqNo = 0
            self.seqNo = 0
            rxNum = 0
        if DEBUG > 1: sys.stderr.write("* comRxHeader() OK\n")
        return rxHeader, rxNum

    def comRxFrame(self, rxNum):
        if DEBUG > 1: sys.stderr.write("* comRxFrame()\n")
        rxFrame = chr(self.DATA_FRAME | rxNum)

        if DEBUG > 2: sys.stderr.write("  comRxFrame() header...\n")
        rxFramedata = self.serialport.read(3)
        if len(rxFramedata) != 3: raise BSLException("Timeout")
        rxFrame = rxFrame + rxFramedata

        if DEBUG > 3: sys.stderr.write("  comRxFrame() check header...\n")
        if rxFrame[1] == chr(0) and rxFrame[2] == rxFrame[3]:   # Add. header info. correct?
            rxLengthCRC = ord(rxFrame[2]) + 2       # Add CRC-Bytes to length
            if DEBUG > 2: sys.stderr.write("  comRxFrame() receiving data, size: %s\n" % rxLengthCRC)

            rxFramedata = self.serialport.read(rxLengthCRC)
            if len(rxFramedata) != rxLengthCRC: raise BSLException("Timeout")
            rxFrame = rxFrame + rxFramedata
            # Check received frame:
            if DEBUG > 3: sys.stderr.write("  comRxFrame() crc check\n")
            # rxLength+4: Length with header but w/o CRC:
            checksum = self.calcChecksum(rxFrame, ord(rxFrame[2]) + 4)
            if rxFrame[ord(rxFrame[2])+4] == chr(0xff & checksum) and \
               rxFrame[ord(rxFrame[2])+5] == chr(0xff & (checksum >> 8)): # Checksum correct?
                # Frame received correctly (=> send next frame)
                if DEBUG > 2: sys.stderr.write("* comRxFrame() OK\n")
                return rxFrame
            else:
                if DEBUG: sys.stderr.write("  comRxFrame() Checksum wrong\n")
        else:
            if DEBUG: sys.stderr.write("  comRxFrame() Header corrupt %r" % rxFrame)
        raise BSLException(self.ERR_COM)            # Frame has errors!

    def comTxHeader(self, txHeader):
        """send header"""
        if DEBUG > 1: sys.stderr.write("* txHeader()\n")
        self.serialport.write(txHeader)

    def comTxRx(self, cmd, dataOut, length):
        """Sends the command cmd with the data given in dataOut to the
        microcontroller and expects either an acknowledge or a frame
        with result from the microcontroller.  The results are stored
        in dataIn (if not a NULL pointer is passed).
        In this routine all the necessary protocol stuff is handled.
        Returns zero if the function was successful."""
        if DEBUG > 1: sys.stderr.write("* comTxRx()\n")
        txFrame     = []
        rxHeader    = 0
        rxNum       = 0

        dataOut = list(dataOut)     # convert to a list for simpler data fill in
        # Transmitting part ----------------------------------------
        # Prepare data for transmit
        if (length % 2) != 0:
            # Fill with one byte to have even number of bytes to send
            if self.protocolMode == self.MODE_BSL:
                dataOut.append(0xFF)  # fill with 0xFF
            else:
                dataOut.append(0)     # fill with zero
            length += 1

        txFrame = "%c%c%c%c" % (self.DATA_FRAME | self.seqNo, cmd, len(dataOut), len(dataOut))

        self.reqNo = (self.seqNo + 1) % self.MAX_FRAME_COUNT

        txFrame = txFrame + string.join(dataOut,'')
        checksum = self.calcChecksum(txFrame, length + 4)
        txFrame = txFrame + chr(checksum & 0xff)
        txFrame = txFrame + chr((checksum >> 8) & 0xff)

        accessAddr = (0x0212 + (checksum^0xffff)) & 0xfffe  # 0x0212: Address of wCHKSUM
        if self.BSLMemAccessWarning and accessAddr < self.BSL_CRITICAL_ADDR:
            sys.stderr.write("WARNING: This command might change data at address %04x or %04x!\n" % (accessAddr, accessAddr + 1))

        self.serialport.flushInput()                #clear receiving queue
        # TODO: Check after each transmitted character,
        # TODO: if microcontroller did send a character (probably a NAK!).
        for c in txFrame:
            self.serialport.write(c)
            if DEBUG > 3: sys.stderr.write("\ttx %02x" % ord(c))
            #if self.serialport.inWaiting(): break  #abort when BSL replies, probably NAK
        else:
            if DEBUG > 1: sys.stderr.write( "  comTxRx() transmit OK\n")

        #Receiving part -------------------------------------------
        if self.ignoreAnswer:
            time.sleep(0.1)
        else:
            rxHeader, rxNum = self.comRxHeader()        # receive header
            if DEBUG > 1: sys.stderr.write("  comTxRx() rxHeader=0x%02x, rxNum=%d, seqNo=%d, reqNo=%s\n" % (rxHeader, rxNum, self.seqNo, self.reqNo))
            if rxHeader == self.DATA_ACK:               # acknowledge/OK
                if DEBUG > 2: sys.stderr.write("  comTxRx() DATA_ACK\n")
                if rxNum == self.reqNo:
                    self.seqNo = self.reqNo
                    if DEBUG > 2: sys.stderr.write("* comTxRx() DATA_ACK OK\n")
                    return          # Acknowledge received correctly => next frame
                raise BSLException(self.ERR_FRAME_NUMBER)
            elif rxHeader == self.DATA_NAK:             # not acknowledge/error
                if DEBUG > 2: sys.stderr.write("* comTxRx() DATA_NAK\n")
                raise BSLException(self.ERR_RX_NAK)
            elif rxHeader == self.DATA_FRAME:           # receive data
                if DEBUG > 2: sys.stderr.write("* comTxRx() DATA_FRAME\n")
                if rxNum == self.reqNo:
                    rxFrame = self.comRxFrame(rxNum)
                    return rxFrame
                raise BSLException(self.ERR_FRAME_NUMBER)
            elif rxHeader == self.CMD_FAILED:           # Frame ok, but command failed.
                if DEBUG > 2: sys.stderr.write("*  comTxRx() CMD_FAILED\n")
                raise BSLException(self.ERR_CMD_FAILED)

        raise BSLException("Unknown header 0x%02x\nAre you downloading to RAM into an old device that requires the patch? Try option -U" % rxHeader)

    def SetRSTpin(self, level=1):
        """Controls RST/NMI pin (0: GND; 1: VCC; unless inverted flag is set)"""
        # invert signal if configured
        if self.invertRST:
            level = not level
        # set pin level
        if self.swapResetTest:
            self.serialport.setRTS(level)
        else:
            self.serialport.setDTR(level)
        # add some delay
        if self.slowmode:
            time.sleep(0.200)
        else:
            time.sleep(0.010)

    def SetTESTpin(self, level=1):
        """Controls TEST pin (inverted on board: 0: VCC; 1: GND; unless inverted flag is set)"""
        # invert signal if configured
        if self.invertTEST:
            level = not level
        # set pin level
        if self.swapResetTest:
            self.serialport.setDTR(level)
        else:
            self.serialport.setRTS(level)
        # make TEST signal on TX pin, unsing break condition.
        # currently only working on win32!
        if self.testOnTX:
            if level:
                serial.win32file.ClearCommBreak(self.serialport.hComPort)
            else:
                serial.win32file.SetCommBreak(self.serialport.hComPort)
        # add some delay
        if self.slowmode:
            time.sleep(0.200)
        else:
            time.sleep(0.010)

    def bslReset(self, invokeBSL=0):
        """Applies BSL entry sequence on RST/NMI and TEST/VPP pins
        Parameters:
            invokeBSL = 1: complete sequence
            invokeBSL = 0: only RST/NMI pin accessed

        RST is inverted twice on boot loader hardware
        TEST is inverted (only once)
        Need positive voltage on DTR, RTS for power-supply of hardware"""
        if DEBUG > 1: sys.stderr.write("* bslReset(invokeBSL=%s)\n" % invokeBSL)
        self.SetRSTpin(1)       # power suply
        self.SetTESTpin(1)      # power suply
        if self.slowmode:
            time.sleep(0.500)   # charge capacitor on boot loader hardware
        else:
            time.sleep(0.250)   # charge capacitor on boot loader hardware

        self.SetRSTpin(0)       # RST  pin: GND
        if invokeBSL:
            self.SetTESTpin(1)  # TEST pin: GND
            self.SetTESTpin(0)  # TEST pin: Vcc
            self.SetTESTpin(1)  # TEST pin: GND
            self.SetTESTpin(0)  # TEST pin: Vcc
            self.SetRSTpin (1)  # RST  pin: Vcc
            if self.testOnTX:
                serial.win32file.ClearCommBreak(self.serialport.hComPort)
            else:
                self.SetTESTpin(1)  # TEST pin: GND
        else:
            self.SetRSTpin(1)   # RST  pin: Vcc
        time.sleep(0.250)       # give MSP430's oscillator time to stabilize

        self.serialport.flushInput()    #clear buffers

    def bslSync(self,wait=0):
        """Transmits Synchronization character and expects to receive Acknowledge character
        if wait is 0 it must work the first time. otherwise if wait is 1
        it is retried (forever).
        """
        loopcnt = 3                                 # Max. tries to get synchronization

        if DEBUG > 1: sys.stderr.write("* bslSync(wait=%d)\n" % wait)
        if self.ignoreAnswer:
            self.serialport.write(chr(self.BSL_SYNC))   # Send synchronization byte
        else:
            while wait or loopcnt:
                loopcnt = loopcnt - 1                   # count down tries
                self.serialport.flushInput()            # clear input, in case a prog is running

                self.serialport.write(chr(self.BSL_SYNC))   # Send synchronization byte
                c = self.serialport.read(1)             # read answer
                if c == chr(self.DATA_ACK):             # ACk
                    if DEBUG > 1: sys.stderr.write("  bslSync() OK\n")
                    return                              # Sync. successful
                elif not c:                             # timeout
                    if DEBUG > 1:
                        if loopcnt:
                            sys.stderr.write("  bslSync() timeout, retry ...\n")
                        else:
                            sys.stderr.write("  bslSync() timeout\n")
                else:                                   # garbage
                    if DEBUG > 1: sys.stderr.write("  bslSync() failed (0x%02x), retry ...\n" % ord(c))
            raise BSLException(self.ERR_BSL_SYNC)       # Sync. failed

    def bslTxRx(self, cmd, addr, length = 0, blkout = None, wait=0):
        """Transmits a command (cmd) with its parameters:
        start-address (addr), length (len) and additional
        data (blkout) to boot loader.
        wait specified if the bsl sync should be tried once or
        repeated, forever
        Parameters return by boot loader are passed via blkin.
        """
        if DEBUG > 1: sys.stderr.write("* bslTxRx()\n")

        if cmd == self.BSL_TXBLK:
            # Align to even start address
            if (addr % 2) != 0:
                addr = addr - 1                     # Decrement address and
                blkout = chr(0xFF) + blkout         # fill first byte of blkout with 0xFF
                length = length + 1
            # Make sure that len is even
            if (length % 2) != 0:
                blkout = blkout + chr(0xFF)         # Inc. len and fill last byte of blkout with 0xFF
                length = length + 1

        elif cmd == self.BSL_RXBLK:
            # Align to even start address
            if (addr % 2) != 0:
                addr = addr - 1                     # Decrement address but
                length = length + 1                 # request an additional byte
            # Make sure that len is even
            if (length % 2) != 0:
                length = length + 1

        if (self.bslVer >= 0x0212) & (cmd == self.BSL_TXBLK) | (cmd == self.BSL_RXBLK):
            if (self.memoffset!=(addr>>16)):
                self.memoffset = (addr>>16)
                self.bslTxRx(self.BSL_SETMEMOFFSET, self.memoffset)
                if DEBUG > 1: sys.stderr.write("   * bslTxRx(): set mem offset 0x%02x\n" % self.memoffset)
            addr &= 0xffff

        # if cmd == self.BSL_TXBLK or cmd == self.BSL_TXPWORD:
        #    length = len + 4

        # Add necessary information data to frame
        if (cmd == self.BSL_SETMEMOFFSET):
            dataOut =  struct.pack("<HH", length, addr)
        else:
            dataOut =  struct.pack("<HH", addr, length)

        if blkout: # Copy data out of blkout into frame
            dataOut = dataOut + blkout

        if DEBUG > 1: sys.stderr.write("   CMD 0x%04x\n" % cmd)
        self.bslSync(wait)                          # synchronize BSL
        rxFrame = self.comTxRx(cmd, dataOut, len(dataOut))  # Send frame
        if rxFrame:                                 # test answer
            return rxFrame[4:] # return only data w/o [hdr,null,len,len]
        else:
            return rxFrame


class BootStrapLoader(LowLevel):
    """Higher level Bootstrap Loader functions."""

    ERR_VERIFY_FAILED       = "Error: verification failed"
    ERR_ERASE_CHECK_FAILED  = "Error: erase check failed"

    ACTION_PROGRAM          = 0x01 # Mask: program data
    ACTION_VERIFY           = 0x02 # Mask: verify data
    ACTION_ERASE_CHECK      = 0x04 # Mask: erase check

    # Max. bytes sent within one frame if parsing a TI TXT file.
    # ( >= 16 and == n*16 and <= MAX_DATA_BYTES!)
    MAXDATA                 = 240-16


    def __init__(self, *args, **kargs):
        LowLevel.__init__(self, *args, **kargs)
        self.byteCtr        = 0
        self.meraseCycles   = 1
        self.patchRequired  = 0
        self.patchLoaded    = 0
        self.bslVer         = 0
        self.passwd         = None
        self.data           = None
        self.maxData        = self.MAXDATA
        self.cpu            = None
        self.showprogess    = 0
        self.retrasnmitPasswd = 1


    def preparePatch(self):
        """Prepare to download patch"""
        if DEBUG > 1: sys.stderr.write("* preparePatch()\n")

        if self.patchLoaded:
            # Load PC with 0x0220.
            # This will invoke the patched bootstrap loader subroutines.
            self.bslTxRx(self.BSL_LOADPC,           # Command: Load PC
                           0x0220)                  # Address to load into PC
            self.BSLMemAccessWarning = 0 # Error is removed within workaround code
        return

    def postPatch(self):
        """Setup after the patch is loaded"""
        if DEBUG > 1: sys.stderr.write("* postPatch()\n")
        if self.patchLoaded:
            self.BSLMemAccessWarning = 1                # Turn warning back on.


    def verifyBlk(self, addr, blkout, action):
        """Verify memory against data or 0xff"""
        if DEBUG > 1: sys.stderr.write("* verifyBlk()\n")

        if action & self.ACTION_VERIFY or action & self.ACTION_ERASE_CHECK:
            if DEBUG: sys.stderr.write("  Check starting at 0x%04x, %d bytes ... \n" % (addr, len(blkout)))

            self.preparePatch()
            blkin = self.bslTxRx(self.BSL_RXBLK, addr, len(blkout))
            self.postPatch()

            for i in range(len(blkout)):
                if action & self.ACTION_VERIFY:
                    # Compare data in blkout and blkin
                    if blkin[i] != blkout[i]:
                        sys.stderr.write("Verification failed at 0x%04x (0x%02x, 0x%02x)\n" % (addr+i, ord(blkin[i]), ord(blkout[i])))
                        sys.stderr.flush()
                        raise BSLException(self.ERR_VERIFY_FAILED)      # Verify failed!
                    continue
                elif action & self.ACTION_ERASE_CHECK:
                    # Compare data in blkin with erase pattern
                    if blkin[i] != chr(0xff):
                        sys.stderr.write("Erase Check failed at 0x%04x (0x%02x)\n" % (addr+i, ord(blkin[i])))
                        sys.stderr.flush()
                        raise BSLException(self.ERR_ERASE_CHECK_FAILED) # Erase Check failed!
                    continue

    def programBlk(self, addr, blkout, action):
        """Programm a memory block"""
        if DEBUG > 1: sys.stderr.write("* programBlk()\n")

        # Check, if specified range is erased
        self.verifyBlk(addr, blkout, action & self.ACTION_ERASE_CHECK)

        if action & self.ACTION_PROGRAM:
            if DEBUG: sys.stderr.write("  Program starting at 0x%05x, %i bytes ...\n" % (addr, len(blkout)))
            self.preparePatch()
            # Program block
            self.bslTxRx(self.BSL_TXBLK, addr, len(blkout), blkout)
            self.postPatch()

        # Verify block
        self.verifyBlk(addr, blkout, action & self.ACTION_VERIFY)

    def progess_update(self, count, total):
        """Textual progress output. Override in subclass to implement a different output"""
        sys.stderr.write("\r%d%%" % (100*count/total))
        sys.stderr.flush()

    def programBlock(self, address, data):
        """Memory write. The block is segmented and downloaded to the target."""
        currentAddr = address
        pstart = 0
        count = 0
        total_length = len(data)
        while pstart < total_length:
            length = self.maxData
            if pstart + length > total_length:
                length = total_length - pstart
            self.programBlk(currentAddr, data[pstart:pstart+length], self.ACTION_PROGRAM | self.ACTION_VERIFY)
            pstart = pstart + length
            currentAddr = currentAddr + length
            #~ self.byteCtr = self.byteCtr + length #total sum
            #~ count = count + length
            #~ if self.showprogess:
                #~ self.progess_update(count, total)
    # segments:
    # list of tuples or lists:
    # segements = [ (addr1, [d0,d1,d2,...]), (addr2, [e0,e1,e2,...])]
    def programData(self, segments, action):
        """Programm or verify data"""
        if DEBUG > 1: sys.stderr.write("* programData()\n")
        count = 0
        #count length if progress updates have to be done
        if self.showprogess:
            total = 0
            for seg in segments:
                total = total + len(seg.data)
        for seg in segments:
            currentAddr = seg.startaddress
            pstart = 0
            while pstart<len(seg.data):
                length = self.maxData
                if pstart+length > len(seg.data):
                    length = len(seg.data) - pstart
                self.programBlk(currentAddr, seg.data[pstart:pstart+length], action)
                pstart = pstart + length
                currentAddr = currentAddr + length
                self.byteCtr = self.byteCtr + length # total sum
                count = count + length
                if self.showprogess:
                    self.progess_update(count, total)

    def uploadData(self, startaddress, size, wait=0):
        """Upload a datablock"""
        if DEBUG > 1: sys.stderr.write("* uploadData()\n")
        data = ''
        pstart = 0
        while pstart<size:
            length = self.maxData
            if pstart+length > size:
                length = size - pstart
            data = data + self.bslTxRx(self.BSL_RXBLK,
                                       pstart+startaddress,
                                       length,
                                       wait=wait)[:-2] # cut away checksum
            pstart = pstart + length
        return data

    def txPasswd(self, passwd=None, wait=0):
        """Transmit password, default if None is given."""
        if DEBUG > 1: sys.stderr.write("* txPassword(%r)\n" % passwd)
        if passwd is None:
            # Send "standard" password to get access to protected functions.
            sys.stderr.write("Transmit default password ...\n")
            sys.stderr.flush()
            # Flash is completely erased, the contents of all Flash cells is 0xff
            passwd = chr(0xff)*32
        else:
            # sanity check of password
            if len(passwd) != 32:
                raise ValueError, "password has wrong length (%d)\n" % len(passwd)
            sys.stderr.write('Transmit password ...\n')
            sys.stderr.flush()
        # send the password
        self.bslTxRx(self.BSL_TXPWORD,      # Command: Transmit Password
                       0xffe0,              # Address of interupt vectors
                       0x0020,              # Number of bytes
                       passwd,              # password
                       wait=wait)           # if wait is 1, try to sync forever


    #-----------------------------------------------------------------

    def actionMassErase(self):
        """Erase the flash memory completely (with mass erase command)"""
        sys.stderr.write("Mass Erase...\n")
        sys.stderr.flush()
        self.bslReset(1)                            # Invoke the boot loader.
        for i in range(self.meraseCycles):
            if i == 1: sys.stderr.write("Additional Mass Erase Cycles...\n")
            self.bslTxRx(self.BSL_MERAS,            # Command: Mass Erase
                                0xfffe,             # Any address within flash memory.
                                0xa506)             # Required setting for mass erase!
        self.passwd = None                          # No password file required!
        # print "Mass Erase complete"
        # Transmit password to get access to protected BSL functions.
        self.txPasswd()

    def actionMainErase(self):
        """Erase the main flash memory only"""
        sys.stderr.write("Main Erase...\n")
        sys.stderr.flush()
        self.bslTxRx(self.BSL_ERASE,                # Command: Segment Erase
                            0xfffe,                 # Any address within flash memory.
                            0xa504)                 # Required setting for main erase!
        self.passwd = None                          # Password gets erased

    def actionSegmentErase(self, address):
        """Erase the memory segemnts. Address parameter is an address within the
        segment to be erased"""
        self.bslTxRx(self.BSL_ERASE,                # Command: Segment Erase
                            address,                # Any address within flash segment.
                            0xa502)                 # Required setting for segment erase!

    def makeActionSegmentErase(self, address):
        """Selective segment erase, the returned object can be called
        to execute the action."""
        class SegmentEraser:
            def __init__(inner_self, segaddr):
                inner_self.address = segaddr
            def __call__(inner_self):
                sys.stderr.write("Erase Segment @ 0x%04x...\n" % inner_self.address)
                sys.stderr.flush()
                self.actionSegmentErase(inner_self.address)
            def __repr__(inner_self):
                return "Erase Segment @ 0x%04x" % inner_self.address
        return SegmentEraser(address)

    def actionStartBSL(self, usepatch=1, adjsp=1, replacementBSL=None, forceBSL=0, mayuseBSL=0, speed=None, bslreset=1):
        """Start BSL, download patch if desired and needed, adjust SP if desired, download
        replacement BSL, change baudrate."""
        sys.stderr.write("Invoking BSL...\n")
        sys.stderr.flush()
        if bslreset:
            self.bslReset(1)                        # Invoke the boot loader.
        self.txPasswd(self.passwd)                  # transmit password

        # Read actual bootstrap loader version.
        # sys.stderr.write("Reading BSL version ...\n")
        blkin = self.bslTxRx(self.BSL_RXBLK,        # Command: Read/Receive Block
                          0x0ff0,                   # Start address
                          16)                       # No. of bytes to read
        dev_id, bslVerHi, bslVerLo = struct.unpack(">H8xBB4x", blkin[:-2]) # cut away checksum and extract data

        if self.cpu is None:                        # cpy type forced?
            if deviceids.has_key(dev_id):
                self.cpu = deviceids[dev_id]        #try to autodectect CPU type
                if DEBUG:
                    sys.stderr.write("Autodetect successful: %04x -> %s\n" % (dev_id, self.cpu))
            else:
                sys.stderr.write("Autodetect failed! Unknown ID: %04x. Trying to continue anyway.\n" % dev_id)
                self.cpu = F1x                      # assume something and try anyway..

        sys.stderr.write("Current bootstrap loader version: %x.%x (Device ID: %04x)\n" % (bslVerHi, bslVerLo, dev_id))
        sys.stderr.flush()
        self.bslVer = (bslVerHi << 8) | bslVerLo

        if self.bslVer <= 0x0110:                   # check if patch is needed
            self.BSLMemAccessWarning = 1
        else:
            self.BSLMemAccessWarning = 0 # Fixed in newer versions of BSL.

        if self.bslVer <= 0x0130 and adjsp:
            # only do this on BSL where it's needed to prevent
            # malfunction with F4xx devices/ newer ROM-BSLs

            # Execute function within bootstrap loader
            # to prepare stack pointer for the following patch.
            # This function will lock the protected functions again.
            sys.stderr.write("Adjust SP. Load PC with 0x0C22 ...\n")
            self.bslTxRx(self.BSL_LOADPC,           # Command: Load PC
                                0x0C22)             # Address to load into PC
            # Re-send password to re-gain access to protected functions.
            self.txPasswd(self.passwd)

        # get internal BSL replacement if needed or forced by the user
        # required if speed is set but an old BSL is in the device
        # if a BSL is given by the user, that one is used and not the internal one
        if ((mayuseBSL and speed and self.bslVer < 0x0150) or forceBSL) and replacementBSL is None:
            replacementBSL = Memory() #File to program
            if self.cpu == F4x:
                if DEBUG:
                    sys.stderr.write("Using built in BSL replacement for F4x devices\n")
                    sys.stderr.flush()
                replacementBSL.loadTIText(cStringIO.StringIO(F4X_BSL))  # parse embedded BSL
            else:
                if DEBUG:
                    sys.stderr.write("Using built in BSL replacement for F1x devices\n")
                    sys.stderr.flush()
                replacementBSL.loadTIText(cStringIO.StringIO(F1X_BSL))  # parse embedded BSL

        # now download the new BSL, if allowed and needed (version lower than the
        # the replacement) or forced
        if replacementBSL is not None:
            self.actionDownloadBSL(replacementBSL)

        # debug message with the real BSL version in use (may have changed after replacement BSL)
        if DEBUG:
            sys.stderr.write("Current bootstrap loader version: 0x%04x\n" % (self.bslVer,))
            sys.stderr.flush()

        # now apply workarounds or patches if BSL in use requires that
        if self.bslVer <= 0x0110:                   # check if patch is needed
            if usepatch:                            # test if patch is desired
                sys.stderr.write("Patch for flash programming required!\n")
                self.patchRequired = 1

                sys.stderr.write("Load and verify patch ...\n")
                sys.stderr.flush()
                # Programming and verification is done in one pass.
                # The patch file is only read and parsed once.
                segments = Memory()                     #data to program
                segments.loadTIText(cStringIO.StringIO(PATCH))  #parse embedded patch
                # program patch
                self.programData(segments, self.ACTION_PROGRAM | self.ACTION_VERIFY)
                self.patchLoaded = 1
            else:
                if DEBUG:
                    sys.stderr.write("Device needs patch, but not applied (usepatch is false).\n")    # message if not patched

        # should the baudrate be changed?
        if speed is not None:
            self.actionChangeBaudrate(speed)            # change baudrate

    def actionDownloadBSL(self, bslsegments):
        """Download and start a new BSL (Devices with 2kB RAM only)"""
        sys.stderr.write("Load new BSL into RAM...\n")
        sys.stderr.flush()
        self.programData(bslsegments, self.ACTION_PROGRAM)
        sys.stderr.write("Verify new BSL...\n")
        sys.stderr.flush()
        self.programData(bslsegments, self.ACTION_VERIFY) # File to verify

        # Read startvector of bootstrap loader
        # blkin = self.bslTxRx(self.BSL_RXBLK, 0x0300, 2)
        # blkin = self.bslTxRx(self.BSL_RXBLK, 0x0220, 2)
        blkin = self.bslTxRx(self.BSL_RXBLK, bslsegments[0].startaddress, 2)
        startaddr = struct.unpack("<H", blkin[:2])[0]

        sys.stderr.write("Starting new BSL at 0x%04x...\n" % startaddr)
        sys.stderr.flush()
        self.bslTxRx(self.BSL_LOADPC,  #Command: Load PC
                     startaddr)        #Address to load into PC

        # BSL-Bugs should be fixed within "new" BSL
        self.BSLMemAccessWarning = 0
        self.patchRequired = 0
        self.patchLoaded   = 0

        # Re-send password to re-gain access to protected functions.
        if self.retrasnmitPasswd:
            self.txPasswd(self.passwd)

        # update version info
        # verison only valid for the internal ones, but it also makes sure
        # that the patches are not applied if the user d/ls one
        self.bslVer = 0x0150

    def actionEraseCheck(self):
        """Check the erasure of required flash cells."""
        sys.stderr.write("Erase Check by file ...\n")
        sys.stderr.flush()
        if self.data is not None:
            self.programData(self.data, self.ACTION_ERASE_CHECK)
        else:
            raise BSLException, "cannot do erase check against data with not knowing the actual data"

    def actionProgram(self):
        """Program data into flash memory."""
        if self.data is not None:
            sys.stderr.write("Program ...\n")
            sys.stderr.flush()
            self.programData(self.data, self.ACTION_PROGRAM)
            sys.stderr.write("%i bytes programmed.\n" % self.byteCtr)
            sys.stderr.flush()
        else:
            raise BSLException, "programming without data not possible"

    def actionVerify(self):
        """Verify programmed data"""
        if self.data is not None:
            sys.stderr.write("Verify ...\n")
            sys.stderr.flush()
            self.programData(self.data, self.ACTION_VERIFY)
        else:
            raise BSLException, "verify without data not possible"

    def actionReset(self):
        """Perform a reset, start user program"""
        sys.stderr.write("Reset device ...\n")
        sys.stderr.flush()
        self.bslReset(0) #only reset

    def actionRun(self, address=0x220):
        """Start program at specified address"""
        sys.stderr.write("Load PC with 0x%04x ...\n" % address)
        sys.stderr.flush()
        self.bslTxRx(self.BSL_LOADPC, # Command: Load PC
                            address)  # Address to load into PC

    # table with values from slaa089a.pdf
    bauratetable = {
        F1x: {
             9600:[0x8580, 0x0000],
            19200:[0x86e0, 0x0001],
            38400:[0x87e0, 0x0002],
            57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
           115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
        },
        F2x: {
             9600:[0x8580, 0x0000],  
            19200:[0x8b00, 0x0001],
            38400:[0x8c80, 0x0002],
        },
        F4x: {
             9600:[0x9800, 0x0000],
            19200:[0xb000, 0x0001],
            38400:[0xc800, 0x0002],
            57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
           115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
        },
    }
    def actionChangeBaudrate(self, baudrate=9600):
        """Change baudrate. The command is sent first, then the comm
        port is reprogrammed. Only possible with newer MSP430-BSL versions.
        (ROM >= 1.6, downloadable >= 1.5)"""
        try:
            baudconfigs = self.bauratetable[self.cpu]
        except KeyError:
            raise ValueError, "unknown CPU type %s, can't switch baudrate" % self.cpu
        try:
            a,l = baudconfigs[baudrate]
        except KeyError:
            raise ValueError, "baudrate not valid. valid values are %r" % baudconfigs.keys()

        sys.stderr.write("Changing baudrate to %d ...\n" % baudrate)
        if baudrate > 38400:
            sys.stderr.write("Note: The selected baudrate is not TI standard! They will not work with TI's BSLs.\n")
        sys.stderr.flush()
        self.bslTxRx(self.BSL_CHANGEBAUD,   # Command: change baudrate
                    a, l)                   # args are coded in adr and len
        time.sleep(0.010)                   # recomended delay
        self.serialport.setBaudrate(baudrate)

    def actionReadBSLVersion(self):
        """Informational output of BSL version number.
        (newer MSP430-BSLs only)"""
        ans = self.bslTxRx(self.BSL_TXVERSION, 0) # Command: receive version info
        # the following values are in big endian style!!!
        family_type, bsl_version = struct.unpack(">H8xH4x", ans[:-2]) # cut away checksum and extract data
        print "Device Type: 0x%04x\nBSL version: 0x%04x\n" % (family_type, bsl_version)
