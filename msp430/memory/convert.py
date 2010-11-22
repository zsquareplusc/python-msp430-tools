#!/usr/bin/env python

# simple converter for hex files
# data can be read from stdin and output on stdout:
# usage: cat file.txt | convert - >out.a43
# usage: convert file.txt >out.a43
# usage: convert file.txt -o out.a43
#
# It is also possible to specify multiple input files and create a single,
# merged output.
#
# (C) 2004-2010 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt

from msp430 import memory
import sys

from optparse import OptionParser

parser = OptionParser(usage='USAGE: %prog [-o filename] [filename...]')

parser.add_option("-o", "--output",
        dest="output",
        help="write result to given file",
        metavar="FILE")

parser.add_option("-i", "--input-format",
        dest="input_format",
        help="input format name (%s)" % (', '.join(memory.load_formats),),
        default="titext",
        metavar="TYPE")

parser.add_option("-f", "--output-format",
        dest="output_format",
        help="output format name (%s)" % (', '.join(memory.save_formats),),
        default="titext",
        metavar="TYPE")

(options, args) = parser.parse_args()

if options.input_format not in memory.load_formats:
    parser.error('Input format %s not supported.' % (options.input_format))

if options.output_format not in memory.save_formats:
    parser.error('Output format %s not supported.' % (options.output_format))

if not args:
    # if no files are given, read from stdin
    args = ['-']

# prepare output
if options.output is None:
    out = sys.stdout
else:
    out = file(options.output, 'wb')

# get input
data = memory.Memory()          # prepare downloaded data

for filename in args:
    if filename == '-':
        data.merge(memory.load(sys.stdin, options.input_format))
    else:
        data.merge(memory.load(filename))

# write ihex file
memory.save(data, out, options.output_format)

