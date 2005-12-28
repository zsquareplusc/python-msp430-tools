#!/usr/bin/env python
# simple TI text to intel hex converter
# data is read from stdin and output on stdout
# usage: cat file.txt | titext2ihex - >out.a43
# usage: titext2ihex file.txt >out.a43
# usage: titext2ihex file.txt -o out.a43
#
# (C) 2004 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# $Id: titext2ihex.py,v 1.3 2005/12/28 22:02:27 cliechti Exp $

from msp430.util import makeihex, _ihexline
from msp430 import memory
import sys

from optparse import OptionParser

parser = OptionParser(usage='usage: %prog [-o filename.a43|-] file.txt|-')
parser.add_option("-o", "--output", dest="output",
                  help="write result to given file", metavar="FILE")
(options, args) = parser.parse_args()

if not args:
    parser.error('no input files given')

#prepare output
if options.output is None or options.output == '-':
    out = sys.stdout
else:
    out = file(options.output, 'wb')

#get input
data = memory.Memory()                      #prepare downloaded data

for filename in args:
    if filename == '-':
        data.loadTIText(sys.stdin)          #TI's format
    else:
        data.loadFile(filename)

#write ihex file
for segment in data:
    makeihex((segment.startaddress, segment.data), eof=0, output=out)
_ihexline(0, [], type=1, output=out)
