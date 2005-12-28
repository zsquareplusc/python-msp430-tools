#!/usr/bin/env python
# simple TI text to intel hex converter
# data is read from stdin and output on stdout
# usage: cat file.txt | titext2ihex >out.a43
#
# (C) 2004 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# $Id: titext2ihex.py,v 1.2 2005/12/28 20:37:57 cliechti Exp $

from msp430.util import hexdump, makeihex, _ihexline
from msp430 import memory
import sys

data = memory.Memory()                      #prepare downloaded data
if len(sys.argv) > 1:
    data.loadFile(sys.argv[1])
else:
    data.loadTIText(sys.stdin)                  #TI's format
for segment in data:
    #~ hexdump((segment.startaddress, segment.data))            #print a hex display
    makeihex((segment.startaddress, segment.data), eof=0)           #ouput a intel-hex file
_ihexline(0, [], type=1)
