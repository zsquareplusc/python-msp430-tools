#!/usr/bin/env python
# JTAG programmer for the MSP430 embedded proccessor.
#
# (C) 2002-2004 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# http://mspgcc.sf.net
#
# Requires Python 2+ and the binary extension _parjtag or ctypes
# and MSP430mspgcc.dll/libMSP430mspgcc.so and HIL.dll/libHIL.so
#
# $Id: msp430-jtag.py,v 1.26 2006/09/03 15:36:21 cliechti Exp $

import sys
from mspgcc import memory, jtag
from mspgcc.util import hexdump, makeihex


VERSION = "2.2"

DEBUG = 0                           #disable debug messages by default

#enumeration of output formats for uploads
HEX             = 0
INTELHEX        = 1
BINARY          = 2


def usage():
    """print some help message"""
    sys.stderr.write("""
USAGE: %(prog)s [options] [file]
Version: %(version)s

If "-" is specified as file the data is read from stdin.
File format is autodetected, unless one of the options below is used.
Prefered file extensions are ".txt" for TI-Text format, ".a43" or ".hex" for
Intel HEX. ELF files can also be loaded.

General options:
  -h, --help            Show this help screen.
  -D, --debug           Increase level of debug messages. This won't be
                        very useful for the average user.
  -I, --intelhex        Force input file format to Intel HEX.
  -T, --titext          Force input file format to be TI-Text.
  --elf                 Force input file format to be ELF.
  -R, --ramsize         Specify the amount of RAM to be used to program
                        flash (default, if --ramsize is not given is
                        autodetect).

Connection:
  -l, --lpt=name        Specify an other parallel port or serial port for the
                        USBFET (the later requires MSP430.dll instead of
                        MSP430mspgcc.dll).
                        (defaults to "LPT1" ("/dev/parport0" on Linux))
  --slowdown=microsecs  Artificially slow down the communication. Can help
                        with long lines, try values between 1 and 50 (parallel
                        port interface with mspgcc's HIL library only).
                        (experts only)

Note: On Windows, use "TIUSB" or "COM5" etc if using MSP430.dll from TI.
      If a MSP430.dll is found it is prefered, otherwise MSP430mspgcc.dll
      is used.
Note: --slowdown > 50 can result in failrures for the ramsize autodetection
      (use --ramsize option to fix this). Use the --debug option and watch
      the outputs. The DCO clock adjustment and thus the Flash timing may be
      inacurate for large values.

Funclets:
  -f, --funclet         The given file is a funclet (a small program to
                        be run in RAM).
  --parameter=<key>=<value>   Pass parameters to funclets.
                        Registers can be written like "R15=123" or "R4=0x55"
                        A string can be written to memory with "0x2e0=hello"
                        --parameter can be given more than once
  --result=value        Read results from funclets. "Rall" reads all registers
                        (case insensitive) "R15" reads R15 etc. Address ranges
                        can be read with "0x2e0-0x2ff". See also --upload.
                        --result can be given more than once.
  --timeout=value       Abort the funclet after the given time in seconds
                        if it does not exit no itself. (default 1)

Note: Writing and/or reading RAM before and/or after running a funclet may not
      work as expected on devices with the JTAG bug like the F123.
Note: Only possible with MSP430mspgcc.dll, not other backends.

Program flow specifiers:
  -e, --masserase       Mass Erase (clear all flash memory).
                        Note: SegmentA on F2xx is NOT erased, that must be
                        done separately with --erase=0x1000
  -m, --mainerase       Erase main flash memory only.
  --eraseinfo           Erase info flash memory only (0x1000-0x10ff).
  --erase=address       Selectively erase segment at the specified address.
  --erase=adr1-adr2     Selectively erase a range of segments.
  -E, --erasecheck      Erase Check by file.
  -p, --program         Program file.
  -v, --verify          Verify by file.
  --secure              Blow JTAG security fuse.
                        Note: This is not reversible, use with care!
                        Note: Not supported with the simple parallel port
                              adapter (7V source required).

The order of the above options matters! The table is ordered by normal
execution order. For the options "E", "p" and "v" a file must be specified.
Program flow specifiers default to "p" if a file is given.
Don't forget to specify "e", "eE" or "m" when programming flash!
"p" already verifies the programmed data, "v" adds an additional
verification through uploading the written data for a 1:1 compare.
No default action is taken if "p" and/or "v" is given, say specifying
only "v" does a "check by file" of a programmed device.

Data retrieving:
  -u, --upload=addr     Upload a datablock (see also: --size).
                        It is also possible to use address ranges. In that
                        case, multiple --upload parameters are allowed.
  -s, --size=num        Size of the data block to upload (Default is 2).
  -x, --hex             Show a hexadecimal display of the uploaded data.
                        This is the default format, see also --bin, --ihex.
  -b, --bin             Get binary uploaded data. This can be used
                        to redirect the output into a file.
  -i, --ihex            Uploaded data is output in Intel HEX format.
                        This can be used to clone a device.

Do before exit:
  -g, --go=address      Start programm execution at specified address.
                        This implies option "w" (wait)
  -r, --reset           Reset connected MSP430. Starts application.
                        This is a normal device reset and will start
                        the programm that is specified in the reset
                        interrupt vector. (see also -g)
  -w, --wait            Wait for <ENTER> before closing parallel port.
  --no-close            Do not close port on exit. Allows to power devices
                        from the parallel port interface.

Address parameters for --erase, --upload, --size can be given in
decimal, hexadecimal or octal.

Examples:
    Mass erase and write file: "%(prog)s -e firmware.elf"
    Dump Information memory: "%(prog)s --upload=0x1000-0x10ff"
""" % {'prog': sys.argv[0], 'version': VERSION})

def parseAddressRange(text):
    """parse a single address or a address range and return a tuple."""
    if '-' in text:
        adr1, adr2 = text.split('-', 1)
        try:
            adr1 = int(adr1, 0)
        except ValueError:
            raise ValueError("Address range start address must be a valid number in dec, hex or octal")
        try:
            adr2 = int(adr2, 0)
        except ValueError:
            raise ValueError("Address range end address must be a valid number in dec, hex or octal")
        return (adr1, adr2)
    else:
        try:
            adr = int(text, 0)
            return (adr, None)
        except ValueError:
            raise ValueError("Address must be a valid number in dec, hex or octal or a range adr1-adr2")


def main():
    global DEBUG
    import getopt
    filetype    = None
    filename    = None
    reset       = 0
    wait        = 0
    goaddr      = None
    jtagobj     = jtag.JTAG()
    toinit      = []
    todo        = []
    startaddr   = None
    size        = 2
    uploadlist  = []
    outputformat= HEX
    lpt         = None
    funclet     = None
    ramsize     = None
    do_close    = 1
    parameters  = []
    results     = []
    timeout     = 1
    quiet       = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],
            "hl:weEmpvrg:Du:d:s:xbiITfR:Sq",
            ["help", "lpt=", "wait"
             "masserase", "erasecheck", "mainerase", "program",
             "erase=", "eraseinfo",
             "verify", "reset", "go=", "debug",
             "upload=", "download=", "size=", "hex", "bin", "ihex",
             "intelhex", "titext", "elf", "funclet", "ramsize=", "progress",
             "no-close", "parameter=", "result=", "timeout=", "secure",
             "quiet", "backend=", "slowdown="]
        )
    except getopt.GetoptError, e:
        # print help information and exit:
        sys.stderr.write("\nError in argument list: %s!\n" % e)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("", "--backend"):
            if a == 'mspgcc':
                backend = jtag.CTYPES_MSPGCC
            elif a == 'parjtag':
                backend = jtag.PARJTAG
            elif a == 'ti':
                backend = jtag.CTYPES_TI
            else:
                raise ValueError("no such backend: %r" % a)
            jtag.init_backend(backend)
        elif o in ("-l", "--lpt"):
            lpt = a
        elif o in ("-w", "--wait"):
            wait = 1
        elif o in ("-e", "--masserase"):
            toinit.append(jtagobj.actionMassErase)      #Erase Flash
        elif o in ("-E", "--erasecheck"):
            toinit.append(jtagobj.actionEraseCheck)     #Erase Check (by file)
        elif o in ("-m", "--mainerase"):
            toinit.append(jtagobj.actionMainErase)      #Erase main Flash
        elif o == "--erase":
            try:
                adr, adr2 = parseAddressRange(a)
                if adr2 is not None:
                    while adr <= adr2:
                        if not (0x1000 <= adr <= 0xffff):
                            sys.stderr.write("Start address is not within Flash memory\n")
                            sys.exit(2)
                        elif adr < 0x1100:
                            modulo = 64     #F2xx XXX: on F1xx/F4xx are segments erased twice
                        elif adr < 0x1200:
                            modulo = 256
                        else:
                            modulo = 512
                        adr = adr - (adr % modulo)
                        toinit.append(jtagobj.makeActionSegmentErase(adr))
                        adr = adr + modulo
                else:
                    toinit.append(jtagobj.makeActionSegmentErase(adr))
            except ValueError, e:
                sys.stderr.write("--erase: %s\n" % e)
                sys.exit(2)
        elif o == "--eraseinfo":
            #F2xx XXX: on F1xx/F4xx are segments erased twice
            toinit.append(jtagobj.makeActionSegmentErase(0x1000))
            toinit.append(jtagobj.makeActionSegmentErase(0x1040))
            toinit.append(jtagobj.makeActionSegmentErase(0x1080))
            toinit.append(jtagobj.makeActionSegmentErase(0x10c0))
        elif o in ("-p", "--program"):
            todo.append(jtagobj.actionProgram)          #Program file
        elif o in ("-v", "--verify"):
            todo.append(jtagobj.actionVerify)           #Verify file
        elif o in ("-r", "--reset"):
            reset = 1
        elif o in ("-g", "--go"):
            try:
                goaddr = int(a, 0)                      #try to convert decimal
            except ValueError:
                sys.stderr.write("Start address must be a valid number in dec, hex or octal\n")
                sys.exit(2)
        elif o in ("-D", "--debug"):
            DEBUG = DEBUG + 1
            try:
                jtagobj.setDebugLevel(DEBUG)
            except IOError:
                sys.stderr.write("Failed to set debug level in backend library\n")
            memory.DEBUG = memory.DEBUG + 1
            jtag.DEBUG = jtag.DEBUG + 1
        elif o in ("-u", "--upload"):
            try:
                start, end = parseAddressRange(a)
                if end is not None:
                    uploadlist.append((start,end))
                else:
                    startaddr = start
            except ValueError, e:
                sys.stderr.write("--upload: %s\n" % e)
                sys.exit(2)
        elif o in ("-s", "--size"):
            try:
                size = int(a, 0)
            except ValueError:
                sys.stderr.write("Size must be a valid number in dec, hex or octal\n")
                sys.exit(2)
        #outut formats
        elif o in ("-x", "--hex"):
            outputformat = HEX
        elif o in ("-b", "--bin"):
            outputformat = BINARY
        elif o in ("-i", "--ihex"):
            outputformat = INTELHEX
        #input formats
        elif o in ("-I", "--intelhex"):
            filetype = 0
        elif o in ("-T", "--titext"):
            filetype = 1
        elif o in ("", "--elf"):
            filetype = 2
        #others
        elif o in ("-f", "--funclet"):
            funclet = 1
        elif o in ("-R", "--ramsize"):
            try:
                ramsize = int(a, 0)
            except ValueError:
                sys.stderr.write("Ramsize must be a valid number in dec, hex or octal\n")
                sys.exit(2)
        elif o in ("-S", "--progress"):
            jtagobj.showprogess = 1
        elif o in ("--no-close", ):
            do_close = 0
        elif o in ("--parameter", ):
            if '=' in a:
                key, value = a.lower().split('=', 2)
                if key[0] == 'r':
                    regnum = int(key[1:])
                    value = int(value, 0)
                    parameters.append((jtagobj.setCPURegister, (regnum, value)))
                else:
                    address = int(key,0)
                    parameters.append((jtagobj.downloadData, (address, value)))
            else:
                sys.stderr.write("Expected <key>=<value> pair in --parameter option, but no '=' found.\n")
                sys.exit(2)
        elif o in ("--result", ):
            a = a.lower()
            if a == 'rall':
                for regnum in range(16):
                    results.append(('R%-2d = 0x%%04x' % regnum, jtagobj.getCPURegister, (regnum,)))
            elif a[0] == 'r':
                regnum = int(a[1:])
                results.append(('R%-2d = 0x%%04x' % regnum, jtagobj.getCPURegister, (regnum,)))
            else:
                try:
                    start, end = parseAddressRange(a)
                    if end is None:
                        end = start
                except ValueError, e:
                    sys.stderr.write("--result: %s\n" % e)
                    sys.exit(2)
                results.append(('0x%04x: %%r' % start, jtagobj.uploadData, (start, end-start)))
        elif o in ("--timeout", ):
            timeout = float(a)
        elif o in ("--secure", ):
            todo.append(jtagobj.actionSecure)
        elif o in ("-q", "--quiet", ):
            quiet = 1
            jtagobj.verbose = 0
        elif o == "--slowdown":
            slowdown = long(a)
            import ctypes
            if sys.platform == 'win32':
                HIL_SetSlowdown = ctypes.windll.HIL.HIL_SetSlowdown
            else:
                # XXX and posix platforms?!
                HIL_SetSlowdown = ctypes.cdll.HIL.HIL_SetSlowdown
            HIL_SetSlowdown = ctypes.windll.HIL.HIL_SetSlowdown
            HIL_SetSlowdown.argtypes  = [ctypes.c_ulong]
            HIL_SetSlowdown.restype   = ctypes.c_int #actually void
            # set slowdown
            HIL_SetSlowdown(slowdown)

    if DEBUG:
        if quiet:
            quiet = 0
            sys.stderr.write("Disabling --quiet as --debug is active\n")

    if not quiet:
        sys.stderr.write("MSP430 JTAG programmer Version: %s\n" % VERSION)

    if len(args) == 0:
        if not quiet:
            sys.stderr.write("Use -h for help\n")
    elif len(args) == 1:                                #a filename is given
        if not funclet:
            if not todo:                                #if there are no actions yet
                todo.insert(0,                          #add some useful actions...
                    jtagobj.actionProgram,
                )
        filename = args[0]
    else:                                               #number of args is wrong
        sys.stderr.write("\nUnsuitable number of arguments\n")
        usage()
        sys.exit(2)

    if DEBUG:   #debug infos
        sys.stderr.write("Debug is level set to %d\n" % DEBUG)
        sys.stderr.write("Python version: %s\n" % sys.version)
        #~ sys.stderr.write("JTAG backend: %s\n" % jtag.backend)


    #sanity check of options
    if goaddr and reset:
        if not quiet:
            sys.stderr.write("Warning: option --reset ignored as --go is specified!\n")
        reset = 0

    if startaddr and reset:
        if not quiet:
            sys.stderr.write("Warning: option --reset ignored as --upload is specified!\n")
        reset = 0
        
    if startaddr and wait:
        if not quiet:
            sys.stderr.write("Warning: option --wait ignored as --upload is specified!\n")
        wait = 0

    #upload ranges and address+size can not be mixed
    if uploadlist and startaddr:
        sys.stderr.write("--upload: Either specify ranges (multiple --upload allowed) or one --upload and one --size\n")
        sys.exit(2)
    #backwards compatibility for old parameter format
    if not uploadlist and startaddr:
        uploadlist.append((startaddr, startaddr+size-1))

    #prepare data to download
    jtagobj.data = memory.Memory()                      #prepare downloaded data
    if filetype is not None:                            #if the filetype is given...
        if filename is None:
            raise ValueError("Filetype but no filename specified")
        if filename == '-':                             #get data from stdin
            file = sys.stdin
        else:
            file = open(filename,"rb")                  #or from a file
        if filetype == 0:                               #select load function
            jtagobj.data.loadIHex(file)                 #intel hex
        elif filetype == 1:
            jtagobj.data.loadTIText(file)               #TI's format
        elif filetype == 2:
            jtagobj.data.loadELF(file)                  #ELF format
        else:
            raise ValueError("Illegal filetype specified")
    else:                                               #no filetype given...
        if filename == '-':                             #for stdin:
            jtagobj.data.loadIHex(sys.stdin)            #assume intel hex
        elif filename:
            jtagobj.data.loadFile(filename)             #autodetect otherwise

    if DEBUG > 5: sys.stderr.write("File: %r\n" % filename)

    # debug messages
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

    abort_due_to_error = 1
    release_done = 0
    jtagobj.open(lpt)                                   #try to open port
    try:
        if ramsize is not None:
            jtagobj.setRamsize(ramsize)

        jtagobj.connect()                               #connect to target

        #initialization list
        if toinit:  #erase and erase check
            if DEBUG: sys.stderr.write("Preparing device ...\n")
            for f in toinit: f()

        #work list
        if todo:
            for f in todo: f()                          #work through todo list

        if reset:                                       #reset device first if desired
            jtagobj.reset()

        for function, args in parameters:
            function(*args)
        
        if funclet is not None:                         #download and start funclet
            jtagobj.actionFunclet(timeout)

        if goaddr is not None:                          #start user programm at specified address
            jtagobj.actionRun(goaddr)                   #load PC and execute

        for format, function, args in results:
            print format % function(*args)

        #upload datablock and output
        if uploadlist:
            if goaddr:                                  #if a program was started...
                raise NotImplementedError
                #TODO:
                #sys.stderr.write("Waiting to device for reconnect for upload: ")
            for start, end in uploadlist:
                size = end - start + 1
                if DEBUG > 2:
                    sys.stderr.write("upload 0x%04x %d Bytes\n" % (start, size))
                data = jtagobj.uploadData(start, size)  #upload data
                if outputformat == HEX:                 #depending on output format
                    hexdump((start, data))              #print a hex display
                elif outputformat == INTELHEX:
                    makeihex((start, data), eof=0)      #ouput a intel-hex file
                else:
                    if sys.platform == "win32":
                        #ensure that the console is in binary mode
                        import os, msvcrt
                        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
                
                    sys.stdout.write(data)              #binary output w/o newline!
            if outputformat == INTELHEX:
                makeihex((0, ''), eof=1)                #finish a intel-hex file
            wait = 0    #wait makes no sense as after upload, the device is still stopped

        if wait:                                        #wait at the end if desired
            jtagobj.reset(1, 1)                         #reset and release target
            release_done = 1
            sys.stderr.write("Press <ENTER> ...\n")     #display a prompt
            sys.stderr.flush()
            raw_input()                                 #wait for newline
    
        abort_due_to_error = 0
    finally:
        if abort_due_to_error:
            sys.stderr.write("Cleaning up after error...\n")
        if not release_done:
            jtagobj.reset(1, 1)                         #reset and release target
        if do_close:
            jtagobj.close()                             #Release communication port
        elif DEBUG:
            sys.stderr.write("WARNING: JTAG port is left open (--no-close)\n")

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise                                           #let pass exit() calls
    except KeyboardInterrupt:
        if DEBUG: raise                                 #show full trace in debug mode
        sys.stderr.write("User abort.\n")               #short messy in user mode
        sys.exit(1)                                     #set errorlevel for script usage
    except Exception, msg:                              #every Exception is caught and displayed
        if DEBUG: raise                                 #show full trace in debug mode
        sys.stderr.write("\nAn error occoured:\n%s\n" % msg) #short messy in user mode
        sys.exit(1)                                     #set errorlevel for script usage
