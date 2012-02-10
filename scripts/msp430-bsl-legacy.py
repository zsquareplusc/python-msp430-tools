#!/usr/bin/env python
# Serial Bootstrap Loader software for the MSP430 embedded proccessor.
#
# (C) 2001-2004 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# http://mspgcc.sf.net
#
# $Id: msp430-bsl.py,v 1.12 2006/04/23 21:28:24 cliechti Exp $

import sys
from msp430.memory.hexdump import hexdump
from msp430.memory import intelhex
from msp430 import memory
from msp430.legacy import bsl

VERSION = "2.0"

DEBUG = 0   # disable debug messages by default

# enumeration of output formats for uploads
HEX             = 0
INTELHEX        = 1
BINARY          = 2

def usage():
    """print some help message"""
    sys.stderr.write("""
USAGE: %s [options] [file]
Version: %s

If "-" is specified as file the data is read from the stdinput.
A file ending with ".txt" is considered to be in TI-Text format,
'.a43' and '.hex' as IntelHex and all other filenames are
considered as ELF files.

General options:
  -h, --help            Show this help screen.
  -c, --comport=port    Specify the communication port to be used.
                        (Default is 0)
                                0->COM1 / ttyS0
                                1->COM2 / ttyS1
                                etc.
  -P, --password=file   Specify a file with the interrupt vectors that
                        are used as password. This can be any file that
                        has previously been used to program the device.
                        (e.g. -P INT_VECT.TXT).
  -f, --framesize=num   Max. number of data bytes within one transmitted
                        frame (16 to 240 in steps of 16) (e.g. -f 240).
  -m, --erasecycles=num Number of mass erase cycles (default is 1). Some
                        old F149 devices need additional erase cycles.
                        On newer devices it is no longer needed. (e.g. for
                        an old F149: -m20)
  -U, --unpatched       Do not download the BSL patch, even when it is
                        needed. This is used when a program is downloaded
                        into RAM and executed from there (and where flash
                        programming is not needed.)
  -D, --debug           Increase level of debug messages. This won't be
                        very useful for the average user...
  -I, --intelhex        Force fileformat to IntelHex
  -T, --titext          Force fileformat to be TI-Text
  -N, --notimeout       Don't use timeout on serial port (use with care)
  -B, --bsl=bsl.txt     Load and use new BSL from the TI Text file
  -S, --speed=baud      Reconfigure speed, only possible with newer
                        MSP403-BSL versions (>1.5, read slaa089a.pdf for
                        details). If the --bsl option is not used, an
                        internal BSL replacement will be loaded.
                        Needs a target with at least 2kB RAM!
                        Possible values are 9600, 19200, 38400
                        (default 9600)
  -1, --f1x             Specify CPU family, in case autodetect fails
  -4, --f4x             Specify CPU family, in case autodetect fails
                        --F1x and --f2x are only needed when the "change
                        baudrate" feature is used and the autodetect feature
                        fails. If the device ID that is uploaded is known, it
                        has precedence to the command line option.
  --invert-reset        Invert signal on RST pin (used for some BSL hardware)
  --invert-test         Invert signal on TEST/TCK pin (used for some BSL
                        hardware)
  --swap-reset-test     Swap the TEST/TCK and RST control signals.
  --test-on-tx          Also toggle TX line for the TEST/TCK signal.
  --ignore-answer       Ignore answers and ACKs from the BSL (dont use unless
                        you know what you do)
  --no-BSL-download     Do not download replacement BSL (disable automatic)
  --force-BSL-download  Download replacement BSL even if not needed (the one
                        in the device would have the required features)

Program Flow Specifiers:
  -e, --masserase       Mass Erase (clear all flash memory)
  -m, --mainerase       Erase main flash memory only (requires --password)
  --erase=address       Selectively erase segment at the specified address
                        (requires --password)
  --erase=adr1-adr2     Selectively erase a range of segments
                        (requires --password)
  -E, --erasecheck      Erase Check by file
  -p, --program         Program file
  -v, --verify          Verify by file

The order of the above options matters! The table is ordered by normal
execution order. For the options "Epv" a file must be specified.
Program flow specifiers default to "pvr" if a file is given.
Don't forget to specify "e" or "eE" when programming flash!

Data retreiving:
  -u, --upload=addr     Upload a datablock (see also: -s).
  -s, --size=num        Size of the data block do upload. (Default is 2)
  -x, --hex             Show a hexadecimal display of the uploaded data.
                        (Default)
  -b, --bin             Get binary uploaded data. This can be used
                        to redirect the output into a file.

Do before exit:
  -g, --go=address      Start programm execution at specified address.
                        This implies option --wait.
  -r, --reset           Reset connected MSP430. Starts application.
                        This is a normal device reset and will start
                        the programm that is specified in the reset
                        vector. (see also -g)
  -w, --wait            Wait for <ENTER> before closing serial port.

Address parameters for --erase, --upload, --size can be given in
decimal, hexadecimal or octal.

If it says "NAK received" it's probably because you specified no or a
wrong password. NAKs during programming indicate that the flash was not
erased before programming.
""" % (sys.argv[0], VERSION))

def legacy_memory(memory):
    # msp430.legacy.bsl doesn't expect seg.data to be type bytearray
    # XXX note this affects the Segments in the memory, no copy is made
    for segment in memory:
        segment.data = bytes(segment.data)
    return memory


# Main:
def main():
    global DEBUG
    import getopt
    filetype    = None
    filename    = None
    comPort     = 0     # Default setting.
    speed       = None
    unpatched   = 0
    reset       = 0
    wait        = 0     # wait at the end
    goaddr      = None
    bslobj      = bsl.BootStrapLoader()
    toinit      = []
    todo        = []
    startaddr   = None
    size        = 2
    outputformat= HEX
    notimeout   = 0
    bslrepl     = None
    mayuseBSL   = 1
    forceBSL    = 0

    sys.stderr.write("MSP430 Bootstrap Loader Version: %s\n" % VERSION)

    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "hc:P:wf:m:eEpvrg:UDudsxbiITNB:S:V14",
            ["help", "comport=", "password=", "wait", "framesize=",
             "erasecycles=", "masserase", "erasecheck", "program",
             "verify", "reset", "go=", "unpatched", "debug",
             "upload=", "download=", "size=", "hex", "bin", "ihex",
             "intelhex", "titext", "notimeout", "bsl=", "speed=",
             "bslversion", "f1x", "f4x", "invert-reset", "invert-test",
             "no-BSL-download", "force-BSL-download", "erase=", "slow",
             "swap-reset-test", "test-on-tx", "ignore-answer"]
        )
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-c", "--comport"):
            try:
                comPort = int(a)                    # try to convert decimal
            except ValueError:
                comPort = a                         # take the string and let serial driver decide
        elif o in ("-P", "--password"):
            # extract password from file
            bslobj.passwd = legacy_memory(memory.load(a)).getMemrange(0xffe0, 0xffff)
        elif o in ("-w", "--wait"):
            wait = 1
        elif o in ("-f", "--framesize"):
            try:
                maxData = int(a)                    # try to convert decimal
            except ValueError:
                sys.stderr.write("Framesize must be a valid number\n")
                sys.exit(2)
            # Make sure that conditions for maxData are met:
            # ( >= 16 and == n*16 and <= MAX_DATA_BYTES!)
            if maxData > bsl.BootStrapLoader.MAX_DATA_BYTES:
                maxData = bsl.BootStrapLoader.MAX_DATA_BYTES
            elif maxData < 16:
                maxData = 16
            bslobj.maxData = maxData - (maxData % 16)
            sys.stderr.write( "Max. number of data bytes within one frame set to %i.\n" % maxData)
        elif o in ("-m", "--erasecycles"):
            try:
                meraseCycles = int(a)              # try to convert decimal
            except ValueError:
                sys.stderr.write("Erasecycles must be a valid number\n")
                sys.exit(2)
            # sanity check of value
            if meraseCycles < 1:
                sys.stderr.write("Erasecycles must be a positive number\n")
                sys.exit(2)
            if meraseCycles > 20:
                sys.stderr.write("Warning: erasecycles set to a large number (>20): %d\n" % meraseCycles)
            sys.stderr.write( "Number of mass erase cycles set to %i.\n" % meraseCycles)
            bslobj.meraseCycles = meraseCycles
        elif o in ("-e", "--masserase"):
            toinit.append(bslobj.actionMassErase)  # Erase entire Flash
        elif o in ("-m", "--mainerase"):
            toinit.append(bslobj.actionMainErase)  # Erase main Flash
        elif o == "--erase":
            if '-' in a:
                adr, adr2 = a.split('-', 1)
                try:
                    adr = int(adr, 0)
                except ValueError:
                    sys.stderr.write("Address range start address must be a valid number in dec, hex or octal\n")
                    sys.exit(2)
                try:
                    adr2 = int(adr2, 0)
                except ValueError:
                    sys.stderr.write("Address range end address must be a valid number in dec, hex or octal\n")
                    sys.exit(2)
                while adr <= adr2:
                    if adr < 0x1100:
                        modulo = 64                # F2xx:64: F1xx, F4xx: 128 (segments get erased twice)
                    elif adr < 0x1200:
                        modulo = 256
                    else:
                        modulo = 512
                    adr = adr - (adr % modulo)
                    toinit.append(bslobj.makeActionSegmentErase(adr))
                    adr = adr + modulo
            else:
                try:
                    seg = int(a, 0)
                    toinit.append(bslobj.makeActionSegmentErase(seg))
                except ValueError:
                    sys.stderr.write("Segment address must be a valid number in dec, hex or octal or a range adr1-adr2\n")
                    sys.exit(2)
        elif o in ("-E", "--erasecheck"):
            toinit.append(bslobj.actionEraseCheck) # Erase Check (by file)
        elif o in ("-p", "--programm"):
            todo.append(bslobj.actionProgram)      # Program file
        elif o in ("-v", "--verify"):
            todo.append(bslobj.actionVerify)       # Verify file
        elif o in ("-r", "--reset"):
            reset = 1
        elif o in ("-g", "--go"):
            try:
                goaddr = int(a)                    # try to convert decimal
            except ValueError:
                try:
                    goaddr = int(a[2:],16)         # try to convert hex
                except ValueError:
                    sys.stderr.write("Go address must be a valid number\n")
                    sys.exit(2)
            wait = 1
        elif o in ("-U", "--unpatched"):
            unpatched = 1
        elif o in ("-D", "--debug"):
            DEBUG = DEBUG + 1
            bsl.DEBUG = bsl.DEBUG + 1
        elif o in ("-u", "--upload"):
            try:
                startaddr = int(a)                  # try to convert decimal
            except ValueError:
                try:
                    startaddr = int(a,16)           # try to convert hex
                except ValueError:
                    sys.stderr.write("Upload address must be a valid number\n")
                    sys.exit(2)
        elif o in ("-s", "--size"):
            try:
                size = int(a)
            except ValueError:
                try:
                    size = int(a,16)
                except ValueError:
                    sys.stderr.write("Size must be a valid number\n")
                    sys.exit(2)
        # outut formats
        elif o in ("-x", "--hex"):
            outputformat = HEX
        elif o in ("-b", "--bin"):
            outputformat = BINARY
        elif o in ("-i", "--ihex"):
            outputformat = INTELHEX
        # input formats
        elif o in ("-I", "--intelhex"):
            filetype = 0
        elif o in ("-T", "--titext"):
            filetype = 1
        # others
        elif o in ("-N", "--notimeout"):
            notimeout = 1
        elif o in ("-B", "--bsl"):
            bslrepl = legacy_memory(memory.load(a)) # File to program
        elif o in ("-V", "--bslversion"):
            todo.append(bslobj.actionReadBSLVersion) # load replacement BSL as first item
        elif o in ("-S", "--speed"):
            try:
                speed = int(a)                      # try to convert decimal
            except ValueError:
                sys.stderr.write("Speed must be decimal number\n")
                sys.exit(2)
        elif o in ("-1", "--f1x"):
            bslobj.cpu = bsl.F1x
        elif o in ("-4", "--f4x"):
            bslobj.cpu = bsl.F4x
        elif o in ("--invert-reset", ):
            bslobj.invertRST = 1
        elif o in ("--invert-test", ):
            bslobj.invertTEST = 1
        elif o in ("--no-BSL-download", ):
            mayuseBSL = 0
        elif o in ("--force-BSL-download", ):
            forceBSL = 1
        elif o in ("--slow", ):
            bslobj.slowmode = 1
        elif o in ("--swap-reset-test", ):
            bslobj.swapResetTest = 1
        elif o in ("--test-on-tx", ):
            bslobj.testOnTX = 1
        elif o in ("--ignore-answer", ):
            bslobj.ignoreAnswer = 1

    if len(args) == 0:
        sys.stderr.write("Use -h for help\n")
    elif len(args) == 1:                            # a filename is given
        if not todo:                                # if there are no actions yet
            todo.extend([                           # add some useful actions...
                bslobj.actionProgram,
                bslobj.actionVerify,
            ])
        filename = args[0]
    else:                                           # number of args is wrong
        usage()
        sys.exit(2)

    if DEBUG:   #debug infos
        sys.stderr.write("Debug level set to %d\n" % DEBUG)
        sys.stderr.write("Python version: %s\n" % sys.version)

    #sanity check of options
    if notimeout and goaddr is not None and startaddr is not None:
        sys.stderr.write("Option --notimeout can not be used together with both --upload and --go\n")
        sys.exit(1)

    if notimeout:
        sys.stderr.write("Warning: option --notimeout can cause improper function in some cases!\n")
        bslobj.timeout = 0

    if goaddr and reset:
        sys.stderr.write("Warning: option --reset ignored as --go is specified!\n")
        reset = 0

    if startaddr and reset:
        sys.stderr.write("Warning: option --reset ignored as --upload is specified!\n")
        reset = 0

    if toinit:
        if DEBUG > 0:       #debug
            #show a nice list of sheduled actions
            sys.stderr.write("TOINIT list:\n")
            for f in toinit:
                try:
                    sys.stderr.write("   %s\n" % f.func_name)
                except AttributeError:
                    sys.stderr.write("   %r\n" % f)
    if todo:
        if DEBUG > 0:       #debug
            #show a nice list of sheduled actions
            sys.stderr.write("TODO list:\n")
            for f in todo:
                try:
                    sys.stderr.write("   %s\n" % f.func_name)
                except AttributeError:
                    sys.stderr.write("   %r\n" % f)

    sys.stderr.flush()

    #prepare data to download
    if filetype is not None:                        # if the filetype is given...
        if filename is None:
            raise ValueError("No filename but filetype specified")
        if filename == '-':                         # get data from stdin
            file = sys.stdin
        else:
            file = open(filename, "rb")             # or from a file
        if filetype == 0:                           # select load function
            bslobj.data = legacy_memory(memory.load(filename, file, 'ihex')) # intel hex
        elif filetype == 1:
            bslobj.data = legacy_memory(memory.load(filename, file, 'titext')) # TI's format
        else:
            raise ValueError("Illegal filetype specified")
    else:                                           # no filetype given...
        if filename == '-':                         # for stdin:
            bslobj.data = legacy_memory(memory.load(filename, sys.stdin, 'ihex')) # assume intel hex
        elif filename:
            bslobj.data = legacy_memory(memory.load(filename)) # autodetect otherwise

    if DEBUG > 3: sys.stderr.write("File: %r" % filename)

    bslobj.comInit(comPort)                         # init port

    #initialization list
    if toinit:  #erase and erase check
        if DEBUG: sys.stderr.write("Preparing device ...\n")
        #bslobj.actionStartBSL(usepatch=0, adjsp=0)     # no workarounds needed
        #if speed: bslobj.actionChangeBaudrate(speed)   # change baud rate as fast as possible
        for f in toinit: f()

    if todo or goaddr or startaddr:
        if DEBUG: sys.stderr.write("Actions ...\n")
        #connect to the BSL
        bslobj.actionStartBSL(
            usepatch=not unpatched,
            replacementBSL=bslrepl,
            forceBSL=forceBSL,
            mayuseBSL=mayuseBSL,
            speed=speed,
        )

    #work list
    if todo:
        for f in todo: f()                          # work through todo list

    if reset:                                       # reset device first if desired
        bslobj.actionReset()

    if goaddr is not None:                          # start user program at specified address
        bslobj.actionRun(goaddr)                    # load PC and execute

    # upload data block and output
    if startaddr is not None:
        if goaddr:                                  # if a program was started...
            # don't restart BSL but wait for the device to enter it itself
            sys.stderr.write("Waiting for device to reconnect for upload: ")
            sys.stderr.flush()
            bslobj.txPasswd(bslobj.passwd, wait=1)     # synchronize, try forever...
            data = bslobj.uploadData(startaddr, size)  # upload data
        else:
            data = bslobj.uploadData(startaddr, size)  # upload data
        if outputformat == HEX:                     # depending on output format
            hexdump( (startaddr, data) )            # print a hex display
        elif outputformat == INTELHEX:
            # output a intel-hex file
            address = startaddr
            start = 0
            while start < len(data):
                end = start + 16
                if end > len(data): end = len(data)
                sys.stdout.write(intelhex._ihexline(address, data[start:end]))
                start += 16
                address += 16
            sys.stdout.write(intelhex._ihexline(0, [], end=True))   # append no data but an end line
        else:
            sys.stdout.write(data)                  # binary output w/o newline!
        wait = 0    # wait makes no sense as after the upload the device is still in BSL

    if wait:                                        # wait at the end if desired
        sys.stderr.write("Press <ENTER> ...\n")     # display a prompt
        sys.stderr.flush()
        raw_input()                                 # wait for newline

    bslobj.comDone()                                # Release serial communication port

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise               #let pass exit() calls
    except KeyboardInterrupt:
        if DEBUG: raise     #show full trace in debug mode
        sys.stderr.write("User abort.\n")   #short messy in user mode
        sys.exit(1)         #set errorlevel for script usage
    except Exception, msg:  #every Exception is caught and displayed
        if DEBUG: raise     #show full trace in debug mode
        sys.stderr.write("\nAn error occoured:\n%s\n" % msg) #short messy in user mode
        sys.exit(1)         #set errorlevel for script usage
