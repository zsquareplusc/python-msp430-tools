"""\
Helper functions to read and write intel hex files.
"""

import sys
import msp430.memory
import msp430.memory.error

def load(filelike):
    """load data from a (opened) file in Intel-HEX format"""
    memory = msp430.memory.Memory()
    segmentdata = []
    currentAddr = 0
    startAddr   = 0
    extendAddr  = 0
    for n, l in enumerate(filelike):
        if not l.strip(): continue  # skip empty lines
        if l[0] != ':': raise msp430.memory.error.FileFormatError(
                "line not valid intel hex data: '%s...'" % l[0:10],
                fileame = getattr(filelike, "name", "<unknown>"),
                lineno = n+1)
        l = l.strip()               # fix CR-LF issues...
        length  = int(l[1:3], 16)
        address = int(l[3:7], 16) + extendAddr
        type    = int(l[7:9], 16)
        check   = int(l[-2:], 16)
        if type == 0x00:
            if currentAddr != address:
                if segmentdata:
                    memory.segments.append(msp430.memory.Segment(startAddr, ''.join(segmentdata)))
                startAddr = currentAddr = address
                segmentdata = []
            for i in range(length):
                segmentdata.append(chr(int(l[9+2*i:11+2*i],16)))
            currentAddr = length + currentAddr
        elif type == 0x02:
            extendAddr = int(l[9:13],16) << 4
        elif type in (0x01, 0x03, 0x04, 0x05):
            pass
        else:
            sys.stderr.write("Ignored unknown field (type 0x%02x) in ihex file.\n" % type)
    if segmentdata:
        memory.segments.append(msp430.memory.Segment(startAddr, ''.join(segmentdata)))
    return memory


def save(memory, filelike):
    """write a string containing intel hex to given file object"""
    noeof=0
    for seg in sorted(memory.segments):
        address = seg.startaddress
        data    = seg.data
        start = 0
        while start < len(data):
            end = start + 16
            if end > len(data): end = len(data)
            filelike.write(_ihexline(address, data[start:end]))
            start += 16
            address += 16
    filelike.write(_ihexline(0, [], end=True))   # append no data but an end line


def _ihexline(address, buffer, end=False):
    """internal use: generate a line with intel hex encoded data"""
    out = []
    if end:
        type = 1
    else:
        type = 0
    out.append( ':%02X%04X%02X' % (len(buffer), address & 0xffff, type) )
    sum = len(buffer) + ((address >> 8) & 255) + (address & 255) + (type & 255)
    for b in [ord(x) for x in buffer]:
        out.append('%02X' % (b & 255))
        sum += b&255
    out.append('%02X\r\n' % ( (-sum) & 255))
    return ''.join(out)

