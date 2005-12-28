#!/usr/bin/env python
# simple intel hex to TI text converter
# data is read from stdin and output on stdout
# usage: cat file.a43 | ihex2titext >out.txt
#
# (C) 2005 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# $Id: ihex2titext.py,v 1.2 2005/12/28 20:37:57 cliechti Exp $

#~ from msp430.util import hexdump
from msp430 import memory
import sys

data = memory.Memory()
if len(sys.argv) > 1:
    data.loadFile(sys.argv[1])
else:
    data.loadIHex(sys.stdin)                    #intel-hex
for segment in data:
    #~ hexdump((segment.startaddress, segment.data))            #print a hex display
    sys.stdout.write("@%04x\n" % segment.startaddress)
    for i in range(0, len(segment.data), 16):
        sys.stdout.write("%s\n" % " ".join(["%02x" % ord(x) for x in segment.data[i:i+16]]))
sys.stdout.write("q\n")
