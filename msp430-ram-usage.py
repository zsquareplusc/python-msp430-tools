#!/usr/bin/env python
"""
This is a little tool to parse msp430-readelf's output and format it nicely.
It can be useful to get an overview of the RAM usage and free stack memory.

Requires:
    Python 2.3+
    mspgcc, msp430-readelf on the path

Chris <cliechti@gmx.net>
"""

import os, re, sys

from optparse import OptionParser

parser = OptionParser()
parser.add_option("-d", "--detailed", dest="detailed", default=False,
    help="print a detailed list of labels", action="store_true")
parser.add_option("-c", "--compact", dest="compact", default=False,
    help="print a compact list of used bytes", action="store_true")
parser.add_option("-q", "--quiet",
    action="store_false", dest="verbose", default=True,
    help="don't print status messages to stdout")

(options, args) = parser.parse_args()

if len(args) != 1:
    parser.error("incorrect number of arguments")



#regexp to parse lines like the following one
#   959: 000002aa     0 OBJECT  GLOBAL DEFAULT    6 rxdata
re_obj = re.compile(r':[ \t]+([0-9a-f]+)[ \t]+([0-9a-f]+)[ \t]+(\w+)[ \t]+.* (.*)$')

#read labeled object from readelf dump
objs = {}
for line in os.popen('msp430-readelf -a -W "%s"' % args[0]):
    #~ print line,
    m = re_obj.search(line)
    if m:
        objs[m.group(4)] = ((int(m.group(1),16), int(m.group(2)), m.group(3)))

#store labels by address
mmap = {}
#~ print 'adr    size name'
for name, (address, size, type) in objs.items():
    #~ print '0x%04x %3d %s %s' % (address, size, name, type)
    if type == 'OBJECT':
        if size == 0: size=1    #make sure zero sized objects are shown too
        for x in range(size):
            if x == 0:
                #first line
                desc = '%s%s (%d)' % (
                    name,
                    (size>1) and '[%s]' % x or '',
                    size,
                )
            else:
                #other lines
                desc = '%s%s' % (
                    ' ' * len(name),
                    (size>1) and '[%s]' % x or ''
                )
            #concatenate if there is more than one label
            if mmap.has_key(address+x):
                desc = '%s | %s' % (mmap[address+x], desc)
            mmap[address+x] = desc

#print labels sorted by address, only RAM
free = 0
for address in range(objs['__data_start'][0], objs['__stack'][0]):
    if mmap.has_key(address):
        name = mmap[address]
    else:
        name = ' -'*20
        free += 1
    if options.detailed:
        print '0x%04x: %s' % (address, name)

if options.compact:
    for address in range(objs['__data_start'][0], objs['__stack'][0], 16):
        print '0x%04x: %s' % (
            address,
            ''.join([mmap.has_key(a) and '*' or '.' 
                     for a in range(address,address+16)])
        )

#scan backwards for continous memory, starting from the stack init
stackmem = 0
address = objs['__stack'][0]
while address >= objs['__data_start'][0] and not mmap.has_key(address):
    address -= 1
    stackmem += 1
#calc total and print summary
size = objs['__stack'][0] - objs['__data_start'][0]
print 'RAM usage summary:'
print '%d of %d bytes used (%d free)' % (size-free, size, free)
print 'the stack can grow up to %d bytes (continous memory at end of RAM)' % (
    stackmem & 0xfffe   #round size, even number
)
