import sys

#for the use with memread
def hexdump( (adr, memstr), output=sys.stdout ):
    """Print a hex dump of data collected with memread
    arg1: tuple with adress, memory
    return None"""
    count = 0
    ascii = ''
    for value in map(ord, memstr):
        if not count: output.write("%04x:  " % adr)
        output.write("%02x " % value)
        ascii += (32 <= value < 128) and chr(value) or '.'
        count += 1
        adr += 1
        if count == 16:
            count = 0
            output.write("   %s\n" % ascii)
            ascii = ''
    if count < 16: output.write("%s   %s\n" % ("   "*(16-count), ascii))


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
    hexdump((0x1000, '0123456789ABCDEF'*3))
    hexdump((0x1000, 'abcdefg'))
