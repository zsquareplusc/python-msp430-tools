#!/usr/bin/env python

"""Test File generator.
This tool generates a hex file, of given size, ending on address
0xffff.

USAGE: hen-ihex.py size_in_kilobyte

The resulting Intel-hex file is output to stdout, use redirection
to save the data to a file.

$Id: gen-ihex.py,v 1.1 2004/02/29 23:06:36 cliechti Exp $
"""

from msp430.util import makeihex

if __name__ == '__main__':
    import struct, sys
    if len(sys.argv) != 2:
        print __doc__
        sys.exit(1)
        
    size = int(sys.argv[1]) #in kilo
    startadr = 0x10000 - 1024*size
    data = ''.join([struct.pack(">H", x) for x in range(startadr, startadr+ 1024*size, 2)])
    print makeihex((startadr, data))
