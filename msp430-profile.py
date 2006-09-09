# statistical profiler for the MSP430

import mspgcc.jtag
import sys
import os
import time

if __name__ == '__main__':
    mspgcc.jtag.init_backend(mspgcc.jtag.CTYPES_MSPGCC)   #doesn't currently work with 3'rd party libs
    samples = [0] * 2**16

    try:
        jtagobj = mspgcc.jtag.JTAG()
        jtagobj.open()                          #try to open port
        try:
            jtagobj.connect()                   #try to connect to target
            connected = True
            jtagobj.reset(1, 0)
            print "profiling..."
            start_time = time.time()
            while True:
                samples[mspgcc.jtag.MSP430_readMAB()] += 1
        finally:
            stop_time = time.time()
            if sys.exc_info()[:1]:              #if there is an exception pending
                jtagobj.verbose = 0             #do not write any more messages
            if connected:
                jtagobj.reset(1, 1)             #reset and release target
            jtagobj.close()                     #release communication port
    except KeyboardInterrupt:
        total = 0
        for n, count in enumerate(samples):
            if count > 0:
                print "0x%04x\t%d" % (n, count)
            total += count
        print '%d samples in %.2f seconds (%d samples/second)' % (
            total,
            stop_time-start_time,
            total / (stop_time-start_time)
        )
