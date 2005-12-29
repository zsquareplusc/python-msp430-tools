#!/usr/bin/env python
#
# MSP430 clock callibration utility.
#
# This tool can measure the internal oscillator of F1xx, F2xx and F4xx devices
# that are connected to the JTAG. It can  display the supported frequencies,
# or run a software FLL to find the settings for a specified frequency.
#
# (C) 2005 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# $Id: msp430-dco.py,v 1.1 2005/12/29 04:00:01 cliechti Exp $

from msp430 import memory, jtag
import sys
import cStringIO
import struct

debug = False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def nice_frequency(frequency):
    """return a string of the frequency with SI unit and a reasonable number
       of digits"""
    if frequency < 1e3:
        return "%dHz" % frequency
    elif frequency < 10e3:
        return "%.3fkHz" % (frequency/1e3)
    elif frequency < 100e3:
        return "%.2fkHz" % (frequency/1e3)
    elif frequency < 1e6:
        return "%.1fkHz" % (frequency/1e3)
    elif frequency < 10e6:
        return "%.3fMHz" % (frequency/1e6)
    elif frequency < 1e9:
        return "%.2fMHz" % (frequency/1e6)
    return "%.2fGHz" % (frequency/1e9)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#see mspgcc cvs/jtag/funclets/counter.S
COUNTER_FUNCLET = """\
@0200
00 02 08 02 22 02 60 07 32 c2 d2 40 fb ff 57 00
d2 40 f4 ff 56 00 0e 43 0f 43 1e 53 0f 63 fd 3f
03 43 ff 3f
q
"""


def getDCOFreq(dcoctl, bcsctl1):
    """measure DCO frequency on a F1xx or F2xx device"""
    funclet = memory.Memory()
    funclet.loadTIText(cStringIO.StringIO(COUNTER_FUNCLET))
    #XXX dcor
    funclet[0].data = funclet[0].data[:6] + chr(dcoctl) + chr(bcsctl1) + funclet[0].data[8:]
    runtime = jtag._parjtag.funclet(funclet[0].data, 100)
    count = jtag._parjtag.regread(14) | (jtag._parjtag.regread(15) << 16)
    return 1000*count*4/runtime

def setDCO(fmin, fmax, maxrsel=7):
    """Software FLL for F1xx and F2xx devices"""
    if debug: sys.stderr.write("setDCO target: %dHz < frequency < %dHz\n" % (fmin, fmax))
    dco = 3<<5
    bcs1 = maxrsel
    fast = True
    upper = False
    lower = False
    
    for tries in range(50):
        if upper and lower and fast:
            if debug: sys.stderr.write("switching to high resolution mode\n")
            fast = False
        frequency = getDCOFreq(dco, bcs1)
        if frequency > fmax:
            if debug: sys.stderr.write("%luHz is too high, decreasing\n" % frequency)
            upper = True
            dco -= fast and 32 or 1
            if dco <= 0:
                dco = 255
                bcs1 -= 1
                if bcs1 <= 0:
                    raise IOError("Couldn't get DCO working with correct frequency.")
        elif frequency < fmin:
            if debug: sys.stderr.write("%luHz is too low, increasing\n" % frequency)
            lower = True
            dco += fast and 32 or 1
            if dco > 255:
                dco = 0
                bcs1 += 1
                if ++bcs1 > 7:
                    raise IOError("Couldn't get DCO working with correct frequency.")
        else:
            if debug: sys.stderr.write("%luHz is OK\n" % frequency)
            return frequency, dco, bcs1
    raise IOError("Couldn't get DCO working with correct frequency.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#see mspgcc cvs/jtag/funclets/counterplus.S
COUNTERPLUS_FUNCLET = """\
@0200
00 02 0c 02 3c 02 00 0e 80 80 00 00 32 c2 72 d0
40 00 d2 40 f4 ff 52 00 d2 40 ed ff 51 00 d2 40
e9 ff 53 00 d2 40 e4 ff 54 00 d2 40 da ff 50 00
0e 43 0f 43 1e 53 0f 63 fd 3f 03 43 ff 3f
q
"""

def getDCOPlusFreq(scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1):
    """measure DCO frequency on a F4xx device"""
    funclet = memory.Memory()
    funclet.loadTIText(cStringIO.StringIO(COUNTERPLUS_FUNCLET))
    funclet[0].data = funclet[0].data[:6] + \
                      chr(scfi0) + chr(scfi1) + \
                      chr(scfqctl) + chr(fll_ctl0) + \
                      chr(fll_ctl1) + funclet[0].data[11:]
    #~ funclet..[0x205] = scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1
    runtime = jtag._parjtag.funclet(funclet[0].data, 100)
    count = jtag._parjtag.regread(14) | (jtag._parjtag.regread(15) << 16)
    return 1000*count*4/runtime

def setDCOPlus(fmin, fmax):
    """Software FLL for F4xx devices"""
    first = 0
    last = 27 << 5
    
    if debug: sys.stderr.write("setDCOPlus target: %dHz < frequency < %dHz\n" % (fmin, fmax))

    # Binary search through the available frequencies, selecting the highest
    # frequency whithin the acceptable range
    while first + 1 < last:
        mid = (last + first) / 2
        # Select DCO range from 0.23MHz to 11.2MHz. Specify frequency via Ndco.
        # Disable Modulation. Enable DCO+.
        frequency = getDCOPlusFreq(mid&3, mid>>2, 0x80, 0x80, 0)
        if frequency > fmax:
            if debug: sys.stderr.write("%luHz is too high, decreasing\n" % frequency)
            last = mid
        elif frequency < fmin:
            if debug: sys.stderr.write("%luHz is too low, increasing\n" % frequency)
            first = mid
        else:
            break

    frequency = getDCOPlusFreq(mid&3, mid>>2, 0x80, 0x80, 0)
    if debug: sys.stderr.write("%luHz\n" % frequency)
    if fmin <= frequency <= fmax:
        return frequency, mid&3, mid>>2, 0x80, 0x80, 0
    raise IOError("Couldn't get DCO working with correct frequency.")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_msp430_type():
    """return the MSP430 type id that is stored in the ROM"""
    (device, ) = struct.unpack(">H", jtag._parjtag.memread(0x0ff0, 2))
    if debug: sys.stderr.write("MSP430 device: 0x%04x\n" % (device, ))
    return device

def adjust_clock(out, frequency, tolerance=0.02):
    """detect MSP430 type and try to set the clock to the given frequency.
    when successful, print the clock control register settings.
    
    this function assumes that the jtag connection to the device has already
    been initialized and that the device is under jtag control and stopped.
    """
    if tolerance < 0.005 or tolerance > 50:
        raise ValueError('tolerance out of range %f' % (tolerance,))
    device = get_msp430_type() >> 8
    if device == 0xf1:
        frequency, dco, bcs1 = setDCO(frequency*(1-tolerance), frequency*(1+tolerance), maxrsel=7)
        out.write('BCSCTL1 = 0x%02x; DCOCTL = 0x%02x; //%dHz\n' % (bcs1, dco, frequency))
    elif device == 0xf2:
        frequency, dco, bcs1 = setDCO(frequency*(1-tolerance), frequency*(1+tolerance), maxrsel=15)
        out.write('BCSCTL1 = 0x%02x; DCOCTL = 0x%02x; //%dHz\n' % (bcs1, dco, frequency))
    elif device == 0xf4:
        frequency, scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1 = setDCOPlus(frequency*(1-tolerance), frequency*(1+tolerance))
        out.write('SCFI0 = 0x%02x; SCFI1 = 0x%02x; SCFQCTL = 0x%02x; FLL_CTL0 = 0x%02x; FLL_CTL1 = 0x%02x; //%dHz\n' % (scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1, frequency))
    else:
        IOError("unknown MSP430 type %2x" % device)

def measure_clock(out):
    """measure fmin and fmax"""
    device = get_msp430_type() >> 8
    if device == 0xf1:
        for rsel in range(8):
            fmin = getDCOFreq(0x00, rsel)
            fmax = getDCOFreq(0xff, rsel)
            out.write('%s < f(rsel_%d) < %s\n' % (nice_frequency(fmin), rsel, nice_frequency(fmax)))
        fmin = getDCOFreq(0, 0)
        fmax = getDCOFreq(0xff, 0x07)
    elif device == 0xf2:
        for rsel in range(16):
            fmin = getDCOFreq(0x00, rsel)
            fmax = getDCOFreq(0xff, rsel)
            out.write('%s < f(rsel_%d) < %s\n' % (nice_frequency(fmin), rsel, nice_frequency(fmax)))
        fmin = getDCOFreq(0, 0)
        fmax = getDCOFreq(0xff, 0x0f)
    elif device == 0xf4:
        fmin = getDCOPlusFreq(0, 0, 0x80, 0x80, 0)
        #XXX the F4xx has clock settings that go higher, but not all are valid
        #for the CPU
        #~ fmax = getDCOPlusFreq(0x03, 0xff, 0x80, 0x80, 0) # should be around 6MHz
        fmax = getDCOPlusFreq(0x13, 0xbf, 0x80, 0x80, 0) # should be around 16MHz
    else:
        IOError("unknown MSP430 type %2x" % device)
    out.write('fmin = %8dHz (%s)\n' % (fmin, nice_frequency(fmin)))
    out.write('fmax = %8dHz (%s)\n' % (fmax, nice_frequency(fmax)))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def main():
    from optparse import OptionParser

    parser = OptionParser(usage="""\
    usage: %prog [options] frequency

MSP430 clock callibration utility.

This tool can measure the internal oscillator of F1xx, F2xx and F4xx devices,
display the supported frequencies, or run a software FLL to find the settings
for a specified frequency.

The target device has to be connected to the JTAG interface.

Examples:
    See min and max clock speeds:
        %prog --measure

    Get clock settings for 2.0MHz +/-2%:
        %prog --tolerance=0.02 2.0e6""")
    parser.add_option("-o", "--output", dest="output",
                      help="write result to given file", metavar="FILE")
    #~ parser.add_option("", "--dcor", dest="dcor",
                      #~ help="use external resistor",
                      #~ default=False, action='store_true')
    parser.add_option("-d", "--debug", dest="debug",
                      help="print debug messages",
                      default=False, action='store_true')
    parser.add_option("-l", "--lpt", dest="lpt",
                      help="set the parallel port",
                      default=None)

    parser.add_option("", "--measure", dest="measure",
                      help="measure min and max clock settings and exit",
                      default=False, action="store_true")

    parser.add_option("-t", "--tolerance", dest="tolerance",
                      help="set the clock tolerance as factor. e.g. 0.1 means 10%",
                      default=0.01, type="float")

    (options, args) = parser.parse_args()

    global debug
    debug = options.debug

    if not options.measure:
        if len(args) != 1:
            parser.error('exacly one argument expected: the target frequency')
        frequency = float(args[0])
    
    #prepare output
    if options.output is None or options.output == '-':
        out = sys.stdout
    else:
        out = file(options.output, 'w')
    
    #
    jtagobj = jtag.JTAG()
    jtagobj.open(options.lpt)               #try to open port
    jtagobj.connect()                       #try to connect to target
    try:
        if options.measure:
            measure_clock(out)
        else:
            adjust_clock(out, frequency, options.tolerance)
        #~ print "%.2f kHz" % (getDCOFreq(0, 0)/1e3)
    finally:
        if sys.exc_info()[:1]:              #if there is an exception pending
            jtagobj.verbose = 0             #do not write any more messages
        jtagobj.reset(1, 1)                 #reset and release target
        jtagobj.close()                     #Release communication port

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise                                           #let pass exit() calls
    except KeyboardInterrupt:
        if debug: raise                                 #show full trace in debug mode
        sys.stderr.write("User abort.\n")               #short messy in user mode
        sys.exit(1)                                     #set errorlevel for script usage
    except Exception, msg:                              #every Exception is caught and displayed
        if debug: raise                                 #show full trace in debug mode
        sys.stderr.write("\nAn error occoured:\n%s\n" % msg) #short messy in user mode
        sys.exit(1)                                     #set errorlevel for script usage    
