# $Id: util.py,v 1.2 2004/07/09 23:18:42 cliechti Exp $

import sys

#for the use with memread
def hexdump( (adr, memstr) ):
    """Print a hex dump of data collected with memread
    arg1: tuple with adress, memory
    return None"""
    count = 0
    ascii = ''
    for value in map(ord, memstr):
        if not count: print "%04x: " % adr,
        print "%02x" % value,
        ascii += (32 <= value < 128) and chr(value) or '.'
        count += 1
        adr += 1
        if count == 16:
            count = 0
            print "  ", ascii
            ascii = ''
    if count < 16: print "   "*(16-count), " ", ascii

def makeihex((address, data), eof=1):
    """work though the data and output lines in inzel hex format.
    and end tag is appended"""
    start = 0
    while start<len(data):
        end = start + 16
        if end > len(data): end = len(data)
        _ihexline(address, [ord(x) for x in data[start:end]])
        start += 16
        address += 16
    if eof:
        _ihexline(address, [], type=1)   #append no data but an end line

def _ihexline(address, buffer, type=0):
    """encode one line, output with checksum"""
    sys.stdout.write( ':%02X%04X%02X' % (len(buffer), address & 0xffff, type) )
    sum = len(buffer) + ((address >> 8) & 255) + (address & 255) + (type&255)
    for b in buffer:
        if b == None: b = 0         #substitute nonexistent values with zero
        sys.stdout.write('%02X' % (b & 255))
        sum += b & 255
    sys.stdout.write('%02X\n' %( (-sum) & 255))

#add some arguments to a function, but don't call it yet, instead return
#a wrapper object for later invocation
class curry:
    """create a callable with some arguments specified in advance"""
    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs
        return apply(self.fun, self.pending + args, kw)

    def __repr__(self):
        #first try if it a function
        try:
            return "curry(%s, %r, %r)" % (self.fun.func_name, self.pending, self.kwargs)
        except AttributeError:
            #fallback for callable classes
            return "curry(%s, %r, %r)" % (self.fun, self.pending, self.kwargs)

if __name__ == '__main__':
    test()
