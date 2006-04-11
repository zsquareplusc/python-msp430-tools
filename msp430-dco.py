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
# $Id: msp430-dco.py,v 1.7 2006/04/11 18:35:23 cliechti Exp $

from mspgcc import memory, jtag, clock
import sys
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

def get_msp430_type():
    """return the MSP430 type id that is stored in the ROM"""
    (device, ) = struct.unpack(">H", jtag._parjtag.memread(0x0ff0, 2))
    if debug: sys.stderr.write("MSP430 device: 0x%04x\n" % (device, ))
    return device

def adjust_clock(out, frequency, tolerance=0.02, dcor=False, define=False):
    """detect MSP430 type and try to set the clock to the given frequency.
    when successful, print the clock control register settings.
    
    this function assumes that the jtag connection to the device has already
    been initialized and that the device is under jtag control and stopped.
    """
    if tolerance < 0.005 or tolerance > 50:
        raise ValueError('tolerance out of range %f' % (tolerance,))
    device = get_msp430_type() >> 8
    
    if device == 0xf1:
        measured_frequency, dco, bcs1 = clock.setDCO(
            frequency*(1-tolerance),
            frequency*(1+tolerance),
            maxrsel=7,
            dcor=dcor
        )
        out.write('// BCS settings for %s\n' % (nice_frequency(measured_frequency), ))
        if define:
            suffix = '_%s' % nice_frequency(frequency).replace('.','_')
            out.write('#define DCOCTL%s 0x%02x\n' % (suffix, dco,))
            out.write('#define BCSCTL1%s 0x%02x\n' % (suffix, bcs1,))
            if dcor:
                out.write('#define BCSCTL2%s 0x01 // select external ROSC\n' % (suffix,))
            else:
                out.write('#define BCSCTL2%s 0x00 // select internal ROSC\n' % (suffix,))
        else:
            out.write('DCOCTL = 0x%02x;\n' % (dco,))
            out.write('BCSCTL1 = 0x%02x;\n' % (bcs1,))
            if dcor:
                out.write('BCSCTL2 = 0x01; // select external ROSC\n')
            else:
                out.write('BCSCTL2 = 0x00; // select internal ROSC\n')
    elif device == 0xf2:
        measured_frequency, dco, bcs1 = clock.setDCO(
            frequency*(1-tolerance),
            frequency*(1+tolerance),
            maxrsel=15,
            dcor=dcor
        )
        out.write('// BCS+ settings for %s\n' % (nice_frequency(measured_frequency), ))
        if define:
            suffix = '_%s' % nice_frequency(frequency).replace('.','_')
            out.write('#define DCOCTL%s 0x%02x\n' % (suffix, dco,))
            out.write('#define BCSCTL1%s 0x%02x\n' % (suffix, bcs1,))
            if dcor:
                out.write('#define BCSCTL2%s 0x01 // select external ROSC\n' % (suffix,))
            else:
                out.write('#define BCSCTL2%s 0x00 // select internal ROSC\n' % (suffix,))
            out.write('#define BCSCTL3%s 0x00\n' % (suffix,))
        else:
            out.write('DCOCTL = 0x%02x;\n' % (dco,))
            out.write('BCSCTL1 = 0x%02x;\n' % (bcs1,))
            if dcor:
                out.write('BCSCTL2 = 0x01; // select external ROSC\n')
            else:
                out.write('BCSCTL2 = 0x00; // select internal ROSC\n')
            out.write('BCSCTL3 = 0x00;\n')
    elif device == 0xf4:
        measured_frequency, scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1 = clock.setDCOPlus(
            frequency*(1-tolerance),
            frequency*(1+tolerance)
        )
        out.write('// FLL+ settings for %s\n' % (nice_frequency(measured_frequency), ))
        if define:
            suffix = '_%s' % nice_frequency(frequency).replace('.','_')
            out.write('#define SCFI0%(suffix)s 0x%(scfi0)02x\n'
                      '#define SCFI1%(suffix)s 0x%(scfi1)02x\n'
                      '#define SCFQCTL%(suffix)s 0x%(scfqctl)02x\n'
                      '#define FLL_CTL0%(suffix)s 0x%(fll_ctl0)02x\n'
                      '#define FLL_CTL1%(suffix)s 0x%(fll_ctl1)02x\n' % vars()
            )
        else:
            out.write('SCFI0 = 0x%02x;\nSCFI1 = 0x%02x;\nSCFQCTL = 0x%02x;\nFLL_CTL0 = 0x%02x;\nFLL_CTL1 = 0x%02x;\n' % (
                scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1
            ))
    else:
        raise IOError("unknown MSP430 type %02x" % device)

def measure_clock(out):
    """measure fmin and fmax"""
    device = get_msp430_type() >> 8
    f_all_max = 0
    f_all_min = 1e99
    if device == 0xf1:
        for rsel in range(8):
            fmin = clock.getDCOFreq(0x00, rsel)
            fmax = clock.getDCOFreq(0xff, rsel)
            out.write('%s <= f(rsel_%d) <= %s\n' % (
                nice_frequency(fmin),
                rsel,
                nice_frequency(fmax)
            ))
            f_all_max = max(fmax, f_all_max)
            f_all_min = min(fmin, f_all_min)
    elif device == 0xf2:
        for rsel in range(16):
            fmin = clock.getDCOFreq(0x00, rsel)
            fmax = clock.getDCOFreq(0xff, rsel)
            out.write('%s <= f(rsel_%d) <= %s\n' % (
                nice_frequency(fmin),
                rsel,
                nice_frequency(fmax)
            ))
            f_all_max = max(fmax, f_all_max)
            f_all_min = min(fmin, f_all_min)
    elif device == 0xf4:
        f_all_min = clock.getDCOPlusFreq(0, 0, 0x80, 0x80, 0)
        #XXX the F4xx has clock settings that go higher, but not all are valid
        #for the CPU
        #~ fmax = getDCOPlusFreq(0x03, 0xff, 0x80, 0x80, 0) # should be around 6MHz
        f_all_max = clock.getDCOPlusFreq(0x13, 0xbf, 0x80, 0x80, 0) # should be around 16MHz
    else:
        raise IOError("unknown MSP430 type %02x" % device)
    out.write('fmin = %8dHz (%s)\n' % (fmin, nice_frequency(f_all_min)))
    out.write('fmax = %8dHz (%s)\n' % (fmax, nice_frequency(f_all_max)))


calibvalues_memory_map = {
    16e6: {'DCO': 0x10F8, 'BCS1': 0x10F9},
    12e6: {'DCO': 0x10FA, 'BCS1': 0x10FB},
    8e6:  {'DCO': 0x10FC, 'BCS1': 0x10FD},
    1e6:  {'DCO': 0x10FE, 'BCS1': 0x10FF},
}

def calibrate_clock(out, tolerance=0.002, dcor=False):
    """curently for F2xx only:
       recalculate the clock calibration values and write them to the flash."""
    device = get_msp430_type() >> 8
    if device == 0xf2:
        #first read the segment form the device, so that only the calibration values
        #are updated. any other data in SegmentA is not changed.
        segment_a = memory.Memory()
        segment_a.append(memory.Segment(0x10c0, jtag._parjtag.memread(0x10c0, 64)))
        #get the settings for all the frequencies
        for frequency in calibvalues_memory_map:
            measured_frequency, dco, bcs1 = clock.setDCO(
                frequency*(1-tolerance),
                frequency*(1+tolerance),
                maxrsel=15,
                dcor=dcor
            )
            out.write('BCS settings for %s: DCOCTL=0x%02x BCSCTL1=0x%02x\n' % (
                nice_frequency(measured_frequency), dco, bcs1)
            )
            segment_a.setMem(calibvalues_memory_map[frequency]['DCO'], chr(dco))
            segment_a.setMem(calibvalues_memory_map[frequency]['BCS1'], chr(bcs1))
        #erase segment and write new values
        jtag._parjtag.memerase(jtag.ERASE_SEGMENT, segment_a[0].startaddress)
        jtag._parjtag.memwrite(segment_a[0].startaddress, segment_a[0].data)
    else:
        raise NotImplementedError("--calibrate is not supported on %Xxx" % device)


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

    Get clock settings for 2.0MHz +/-1%:
        %prog --tolerance=0.01 2.0e6
    
Use it at your own risk. No guarantee that the values are correct.""")
    parser.add_option("-o", "--output", dest="output",
                      help="write result to given file", metavar="FILE",
                      default=None)
    parser.add_option("", "--dcor", dest="dcor",
                      help="use external resistor",
                      default=False, action='store_true')
    parser.add_option("-d", "--debug", dest="debug",
                      help="print debug messages",
                      default=False, action='store_true')
    parser.add_option("-l", "--lpt", dest="lpt",
                      help="set the parallel port",
                      default=None)

    parser.add_option("-m", "--measure", dest="measure",
                      help="measure min and max clock settings and exit",
                      default=False, action="store_true")


    parser.add_option("-c", "--calibrate", dest="calibrate",
                      help="Restore calibration values on F2xx devices",
                      default=False, action="store_true")
                      
    parser.add_option("-t", "--tolerance", dest="tolerance",
                      help="set the clock tolerance as factor. e.g. 0.01 means 1% (default=0.005)",
                      default=0.005, type="float")

    parser.add_option("", "--define", dest="define",
                      help="output #defines instead of assignments",
                      default=False, action='store_true')

    (options, args) = parser.parse_args()

    global debug
    debug = options.debug
    clock.debug = options.debug

    if not (options.measure or options.calibrate):
        if len(args) != 1:
            parser.error('exactly one argument expected: the target frequency')
        frequency = float(args[0])
    
    #prepare output
    if options.output is None or options.output == '-':
        out = sys.stdout
    else:
        out = file(options.output, 'w')
    
    #
    jtag.init_backend(jtag.CTYPES_MSPGCC)   #doesn't currently work with 3'rd party libs
    jtagobj = jtag.JTAG()
    jtagobj.open(options.lpt)               #try to open port
    jtagobj.connect()                       #try to connect to target
    try:
        if options.measure:
            measure_clock(out)
        elif options.calibrate:
            calibrate_clock(
                out,
                options.tolerance,
                options.dcor,
            )
        else:
            adjust_clock(
                out,
                frequency,
                options.tolerance,
                options.dcor,
                options.define
            )
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
