#!/usr/bin/env python
#
# JTAG programmer for the MSP430 embedded processor.
#
# (C) 2002-2010 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# Requires Python 2+ and the binary extension _parjtag or ctypes
# and MSP430mspgcc.dll/libMSP430mspgcc.so or MSP430.dll/libMSP430.so
# and HIL.dll/libHIL.so

import sys
from msp430 import memory
from msp430.jtag import jtag
from msp430.memory import hexdump


VERSION = "3.0"

DEBUG = __debug__                      # disable debug messages by default


def help_on_backends():
    sys.stderr.write("""\
%(prog)s can use different libraries to connect to the target.
The backend can be chosen with the --backend command line option.

"mspgcc"
    Using %(msp430mspgcc)s, the open source implementation
    from the mspgcc project.

"ti" (default)
    Using %(msp430)s, the proprietary library from TI or a
    compatible one from a 3rd party supplier.

"parjtag"
    Old way of using %(msp430mspgcc)s. Use "mspgcc" instead.

Software support for interfaces:
    +============================+==========+==========+==========+
    | device JTAG                |  mspgcc  |         ti          |
    | capabilities               |   FET    |   FET    | USB-FET  |
    +============================+==========+==========+==========+
    | standard    / 4 wire       |   yes    |   yes    |   yes    |
    +----------------------------+----------+----------+----------+
    | spy-bi-wire / 4 wire (1)   |  yes(2)  |   no     |  yes(3)  |
    +----------------------------+----------+----------+----------+
    | spy-bi-wire / 2 wire       |   no     |   no     |  yes(4)  |
    +============================+==========+==========+==========+

Notes:
    (1) 4 wire JTAG on devices with spy-bi-wire capability needs special
        timings.
    (2) Timing critical, may not work on all machines or at every try.
    (3) Using --spy-bi-wire-jtag option.
    (4) Using --spy-bi-wire option.

Features of backends:
    +=======================================+==========+==========+
    | Feature                               |  mspgcc  |   ti     |
    +=======================================+==========+==========+
    | Support for USB JTAG adapters         |   no     |   yes    |
    +---------------------------------------+----------+----------+
    | Using --funclet option                |   yes    |   no     |
    +=======================================+==========+==========+

""" % { 
        'prog': sys.argv[0],
        'msp430': (sys.platform != 'win32') and 'libMSP430.so' or 'MSP430.dll',
        'msp430mspgcc': (sys.platform != 'win32') and 'libMSP430mspgcc.so' or 'MSP430mspgcc.dll',
    })


def parseAddressRange(text):
    """parse a single address or an address range and return a tuple."""
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
    elif '/' in text:
        adr1, size = text.split('/', 1)
        try:
            adr1 = int(adr1, 0)
        except ValueError:
            raise ValueError("Address range start address must be a valid number in dec, hex or octal")
        multiplier = 1
        if size.endswith('k'):
            size = size[:-1]
            multiplier = 1024
        try:
            size = int(size, 0) * multiplier
        except ValueError:
            raise ValueError("Address range size must be a valid number in dec, hex or octal")
        return (adr1, adr1 + size - 1)
    else:
        try:
            adr = int(text, 0)
            return (adr, None)
        except ValueError:
            raise ValueError("Address must be a valid number in dec, hex or octal or a range adr1-adr2")


def main():
    from optparse import OptionParser, OptionGroup, IndentedHelpFormatter, TitledHelpFormatter

    # i dont like how texts are re-wrapped and paragraphs are joined. get rid
    # of that
    class Formatter(TitledHelpFormatter):
        def format_description(self, description):
            return description

    parser = OptionParser(usage="""\
%prog [OPTIONS] [FILE [FILE...]]

Version: %version

If "-" is specified as file the data is read from stdin and TI-text format
is expected by default.
""",
                formatter=Formatter(),
                version=VERSION)

    vars = {
        'prog': sys.argv[0],
        'version': VERSION,
        'msp430': (sys.platform != 'win32') and 'libMSP430.so' or 'MSP430.dll',
        'msp430mspgcc': (sys.platform != 'win32') and 'libMSP430mspgcc.so' or 'MSP430mspgcc.dll',
    }

    parser.add_option("--help-backend",
            dest="help_backend",
            help="show help about the different backends",
            default=False,
            action='store_true')

    parser.add_option("-d", "--debug",
            dest="debug",
            help="print debug messages",
            default=False,
            action='store_true')

    parser.add_option("-v", "--verbose",
            dest="verbose",
            help="show more messages (can be given multiple times)",
            default=0,
            action='count')

    parser.add_option("-q", "--quiet",
            dest="quiet",
            help="suppress all messages",
            default=False,
            action='store_true')

    parser.add_option("-R", "--ramsize",
            dest="ramsize",
            type="int",
            help="specify the amount of RAM to be used to program flash (default: auto detected)",
            default=None)

    group = OptionGroup(parser, "Programing", """\
File format is auto detected, unless --input-format is used.
Preferred file extensions are ".txt" for TI-Text format, ".a43" or ".hex" for
Intel HEX. ELF files can also be loaded.
""")

    group.add_option("-i", "--input-format",
            dest="input_format",
            help="input format name (%s)" % (', '.join(memory.load_formats),),
            default=None,
            metavar="TYPE")

    group.add_option("-S", "--progress",
            dest="progress",
            help="show progress while programming",
            default=False,
            action='store_true')

    parser.add_option_group(group)

    group = OptionGroup(parser, "Connection", """\
Note: On Windows, use "USB", "TIUSB" or "COM5" etc if using MSP430.dll from TI.
      On other platforms, e.g. Linux, use "/dev/ttyUSB0" etc. if using
      libMSP430.so.
      If a %(msp430)s is found, it is preferred, otherwise
      %(msp430mspgcc)s is used.

Note: --slowdown > 50 can result in failures for the RAM size auto detection
      (use --ramsize option to fix this). Use the --verbose option and watch
      the outputs. The DCO clock adjustment and thus the Flash timing may be
      inaccurate for large values.
""" % vars)

    group.add_option("--backend",
            dest="backend",
            help="select an alternate backend. See --help-backend for more information",
            default=None)

    group.add_option("-l", "--lpt",
            dest="port_name",
            metavar="PORT",
            help='specify an other parallel port or serial port for the USBFET (the later requires %(msp430)s instead of %(msp430mspgcc)s).  (defaults to "LPT1" ("/dev/parport0" on Linux))' % vars,
            default=None)

    group.add_option("--spy-bi-wire-jtag",
            dest="spy_bi_wire_jtag",
            help="interface is 4 wire on a spy-bi-wire capable device",
            default=False,
            action='store_true')

    group.add_option("--spy-bi-wire",
            dest="spy_bi_wire",
            help="interface is 2 wire on a spy-bi-wire capable device",
            default=False,
            action='store_true')

    group.add_option("--slowdown",
            dest="slowdown",
            metavar="MICROSECONDS",
            help="artificially slow down the communication. Can help with long lines, try values between 1 and 50 (parallel port interface with mspgcc's HIL library only). (experts only)",
            default=None)

    parser.add_option_group(group)

    group = OptionGroup(parser, "Funclets", """\
Note: Writing and/or reading RAM before and/or after running a funclet may not
      work as expected on devices with the JTAG bug like the F123.

Note: Only possible with %(msp430mspgcc)s, not other backends.
""" % vars)

    group.add_option("--funclet",
            dest="funclet",
            help="the given file is a funclet (a small program to be run in RAM)",
            default=None,
            metavar="FILENAME")

    group.add_option("--parameter",
            dest="funclet_parameter",
            metavar="<KEY>=<VALUE>",
            help='Pass parameters to funclets. Registers can be written like "R15=123" or "R4=0x55" A string can be written to memory with "0x2e0=hello" --parameter can be given more than once',
            default=[],
            action='append')

    group.add_option("--result",
            dest="funclet_result",
            metavar="VALUE",
            help='Read results from funclets. "Rall" reads all registers (case insensitive) "R15" reads R15 etc. Address ranges can be read with "0x2e0-0x2ff". See also --upload.  --result can be given more than once.',
            default=[],
            action='append')

    group.add_option("--timeout",
            dest="funclet_timeout",
            metavar="VALUE",
            type="float",
            help='Abort the funclet after the given time in seconds if it does not exit no itself. (default 1)',
            default=1)

    parser.add_option_group(group)

    group = OptionGroup(parser, "Program flow specifiers", """\
Program flow specifiers default to "-P" if a file is given.
Don't forget to specify "-e", "-eE" or "-m" when programming flash!

"-P" already verifies the programmed data, "-V" adds an additional
verification through uploading the written data for a 1:1 compare.

No default action is taken if "-P" and/or "-V" is given, say specifying
only "-V" does a "check by file" of a programmed device.

Multiple --erase options are allowed. It is possible to use address
ranges such as 0xf000-0xf0ff or 0xf000/4k.

NOTE: SegmentA on F2xx is NOT erased with --masserase, that must be
      done separately with --erase=0x10c0 or --eraseinfo".
""")

    group.add_option("-e", "--masserase",
            dest="do_mass_erase",
            help="mass erase (clear all flash memory)",
            default=False,
            action='store_true')

    group.add_option("-m", "--mainerase",
            dest="do_main_erase",
            help="erase main flash memory only",
            default=False,
            action='store_true')

    group.add_option("--eraseinfo",
            dest="do_info_erase",
            help="erase info flash memory only (0x1000-0x10ff)",
            default=False,
            action='store_true')

    group.add_option("--erase",
            dest="erase_list",
            help="selectively erase segment at the specified address or address range",
            default=[],
            action='append')

    group.add_option("-E", "--erasecheck",
            dest="do_erase_check",
            help="erase check by file",
            default=False,
            action='store_true')

    group.add_option("-P", "--program",
            dest="do_program",
            help="program file",
            default=False,
            action='store_true')

    group.add_option("-V", "--verify",
            dest="do_verify",
            help="verify by file",
            default=False,
            action='store_true')

    parser.add_option_group(group)

    group = OptionGroup(parser, "JTAG fuse", """\
WARNING: This is not reversible, use with care!  Note: Not supported with the
         simple parallel port adapter (7V source required).",
""")

    group.add_option("--secure",
            dest="do_secure",
            help="blow JTAG security fuse",
            default=False,
            action='store_true')

    parser.add_option_group(group)

    group = OptionGroup(parser, "Data retrieving", """\
It is possible to use address ranges such as 0xf000-0xf0ff or 0xf000/256.
Multiple --upload options are allowed.
""")

    group.add_option("-u", "--upload",
            dest="upload_list",
            metavar="ADDRESS",
            help='upload a data block, can be passed multiple times',
            default=[],
            action='append')

    group.add_option("-o", "--output",
            dest="output",
            help="write result to given file",
            metavar="DESTINATION")

    group.add_option("-f", "--output-format",
            dest="output_format",
            help="output format name (%s)" % (', '.join(memory.save_formats),),
            default="hex",
            metavar="TYPE")

    parser.add_option_group(group)

    group = OptionGroup(parser, "Do before exit")

    group.add_option("-g", "--go",
            dest="do_run",
            metavar="ADDRESS",
            type="int",
            help='start program execution at specified address, this implies option --wait',
            default=None,
            action='store')

    group.add_option("-r", "--reset",
            dest="do_reset",
            help="perform a normal device reset that will start the program that is specified in the reset interrupt vector",
            default=False,
            action='store_true')

    group.add_option("-w", "--wait",
            dest="wait",
            help="wait for <ENTER> before closing the port",
            default=False,
            action='store_true')

    group.add_option("--no-close",
            dest="no_close",
            help="do not close port on exit, allows to power devices from the parallel port interface",
            default=False,
            action='store_true')

    parser.add_option_group(group)

    group = OptionGroup(parser, "Examples", """\
Mass erase and program from file: "%(prog)s -e firmware.elf"
Dump information memory: "%(prog)s --upload=0x1000-0x10ff"
""" % vars)
    parser.add_option_group(group)

    (options, args) = parser.parse_args()

    if options.input_format is not None and options.input_format not in memory.load_formats:
        parser.error('Input format %s not supported.' % (options.input_format))

    if options.output_format not in memory.save_formats:
        parser.error('Output format %s not supported.' % (options.output_format))


    reset       = False
    goaddr      = None
    jtagobj     = jtag.JTAG()
    toinit      = []
    todo        = []
    uploadlist  = []
    funclet     = None
    parameters  = []
    results     = []


    if options.help_backend:
        help_on_backends()
        sys.exit()

    if options.backend is not None:
        if options.backend == 'mspgcc':
            backend = jtag.CTYPES_MSPGCC
        elif options.backend == 'parjtag':
            backend = jtag.PARJTAG
        elif options.backend == 'ti':
            backend = jtag.CTYPES_TI
        else:
            raise parser.error("no such backend: %r" % options.backend)
        jtag.init_backend(backend)

    if options.spy_bi_wire:
        jtag.interface = 'spy-bi-wire'
    if options.spy_bi_wire_jtag:
        jtag.interface = 'spy-bi-wire-jtag'


    if options.do_mass_erase:
        toinit.append(jtagobj.actionMassErase)      # Erase Flash
    if options.do_main_erase:
        toinit.append(jtagobj.actionMainErase)      # Erase main Flash
    for a in options.erase_list:
        try:
            adr, adr2 = parseAddressRange(a)
            if adr2 is not None:
                while adr <= adr2:
                    if not (0x1000 <= adr <= 0xffff):
                        sys.stderr.write("Start address is not within Flash memory\n")
                        sys.exit(2)
                    elif adr < 0x1100:
                        modulo = 64     # F2xx XXX: on F1xx/F4xx are segments erased twice
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
            parser.error("--erase: %s" % e)
    if options.do_info_erase:
        # F2xx XXX: on F1xx/F4xx are segments erased twice
        toinit.append(jtagobj.makeActionSegmentErase(0x1000))
        toinit.append(jtagobj.makeActionSegmentErase(0x1040))
        toinit.append(jtagobj.makeActionSegmentErase(0x1080))
        toinit.append(jtagobj.makeActionSegmentErase(0x10c0))
    if options.do_erase_check:
        toinit.append(jtagobj.actionEraseCheck)     # Erase Check (by file)

    if options.do_program:
        todo.append(jtagobj.actionProgram)          # Program file
    if options.do_verify:
        todo.append(jtagobj.actionVerify)           # Verify file
    if options.do_secure:
        todo.append(jtagobj.actionSecure)
    if options.do_reset:
        reset = True

    if options.debug:
        global DEBUG
        DEBUG = True
    if options.verbose:
        try:
            jtagobj.setDebugLevel(options.verbose)
        except IOError:
            sys.stderr.write("WARNING: Failed to set debug level in backend library\n")
        memory.DEBUG = options.verbose
        jtag.DEBUG = options.verbose

    for a in options.upload_list:
        try:
            start, end = parseAddressRange(a)
            if end is not None:
                uploadlist.append((start, end))
            else:
                uploadlist.append((start, start+15))
        except ValueError, e:
            parser.error("--upload: %s" % e)

    # others
    if options.funclet:
        funclet = True

    if options.progress:
        jtagobj.showprogess = 1

    for a in options.funclet_parameter:
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
            parser.erro("Expected <key>=<value> pair in --parameter option, but no '=' found.")

    for a in options.funclet_result:
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
                parser.error("--result: %s" % e)
            results.append(('0x%04x: %%r' % start, jtagobj.uploadData, (start, end-start)))

    if options.quiet:
        jtagobj.verbose = 0

    if options.slowdown is not None:
        import ctypes
        if sys.platform == 'win32':
            HIL_SetSlowdown = ctypes.windll.HIL.HIL_SetSlowdown
        else:
            # XXX and posix platforms?!
            HIL_SetSlowdown = ctypes.cdll.HIL.HIL_SetSlowdown
        HIL_SetSlowdown = ctypes.windll.HIL.HIL_SetSlowdown
        HIL_SetSlowdown.argtypes  = [ctypes.c_ulong]
        #~ HIL_SetSlowdown.restype   = ctypes.c_int # actually void
        # set slowdown
        HIL_SetSlowdown(options.slowdown)


    if options.verbose:
        if options.quiet:
            options.quiet = False
            sys.stderr.write("Disabling --quiet as --verbose is active\n")

    if not options.quiet:
        sys.stderr.write("MSP430 JTAG programmer Version: %s\n" % VERSION)

    if not args:
        if not options.quiet:
            sys.stderr.write("Use -h for help\n")
    elif args:                                          # a filename is given
        if not funclet:
            if not todo:                                # if there are no actions yet
                todo.insert(0, jtagobj.actionProgram)   # add some useful actions...
    else:                                               # number of args is wrong
        sys.stderr.write("\nUnsuitable number of arguments\n")
        usage()
        sys.exit(2)

    if options.verbose:   # debug infos
        sys.stderr.write("Debug is %s\n" % DEBUG)
        sys.stderr.write("Verbosity level set to %d\n" % options.verbose)
        sys.stderr.write("Python version: %s\n" % sys.version)
        #~ sys.stderr.write("JTAG backend: %s\n" % jtag.backend)


    # sanity check of options
    if goaddr and reset:
        if not options.quiet:
            sys.stderr.write("Warning: option --reset ignored as --go is specified!\n")
        reset = False

    if options.upload_list and reset:
        if not options.quiet:
            sys.stderr.write("Warning: option --reset ignored as --upload is specified!\n")
        reset = False

    if options.upload_list and options.wait:
        if not options.quiet:
            sys.stderr.write("Warning: option --wait ignored as --upload is specified!\n")
        options.wait = False


    # prepare output
    if options.output is None:
        out = sys.stdout
        if sys.platform == "win32":
            # ensure that the console is in binary mode
            import os, msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    else:
        out = file(options.output, 'wb')

    # prepare data to download
    data = memory.Memory()                  # prepare downloaded data

    for filename in args:
        if filename == '-':
            data.merge(memory.load('<stdin>', sys.stdin, format=options.input_format or "titext"))
        else:
            data.merge(memory.load(filename, format=options.input_format))

    jtagobj.data = data                     # prepare downloaded data

    if options.verbose > 5: sys.stderr.write("File(s): %r\n" % args)

    # debug messages
    if toinit:
        if options.verbose:       # debug
            # show a nice list of scheduled actions
            sys.stderr.write("TOINIT list:\n")
            for f in toinit:
                try:
                    sys.stderr.write("   %s\n" % f.func_name)
                except AttributeError:
                    sys.stderr.write("   %r\n" % f)
    if todo:
        if options.verbose:       # debug
            # show a nice list of scheduled actions
            sys.stderr.write("TODO list:\n")
            for f in todo:
                try:
                    sys.stderr.write("   %s\n" % f.func_name)
                except AttributeError:
                    sys.stderr.write("   %r\n" % f)

    sys.stderr.flush()

    abort_due_to_error = 1
    release_done = 0
    jtagobj.open(options.port_name)                     # try to open port
    try:
        if options.ramsize is not None:
            jtagobj.setRamsize(options.ramsize)

        jtagobj.connect()                               # connect to target

        # initialization list
        if toinit:  # erase and erase check
            if options.verbose: sys.stderr.write("Preparing device ...\n")
            for f in toinit: f()

        # work list
        if todo:
            for f in todo: f()                          # work through TODO list

        if reset:                                       # reset device first if desired
            jtagobj.reset()

        for function, args in parameters:
            function(*args)

        if funclet is not None:                         # download and start funclet
            jtagobj.actionFunclet(options.timeout)

        if goaddr is not None:                          # start user program at specified address
            jtagobj.actionRun(goaddr)                   # load PC and execute

        for format, function, args in results:
            print format % function(*args)

        # upload data block and output
        if uploadlist:
            if goaddr:                                  # if a program was started...
                raise NotImplementedError
                # TODO:
                # sys.stderr.write("Waiting to device for reconnect for upload: ")
            data = memory.Memory()
            for start, end in uploadlist:
                size = end - start + 1
                if options.verbose > 2:
                    sys.stderr.write("Upload 0x%04x %d bytes\n" % (start, size))
                data.append(memory.Segment(start, jtagobj.uploadData(start, size)))  # upload data
            memory.save(data, out, options.output_format)
            options.wait = False   # wait makes no sense as after upload, the device is still stopped

        if options.wait:                                # wait at the end if desired
            jtagobj.reset(1, 1)                         # reset and release target
            release_done = 1
            if not options.quiet:
                sys.stderr.write("Press <ENTER> ...\n") # display a prompt
                sys.stderr.flush()
            raw_input()                                 # wait for newline

        abort_due_to_error = 0
    finally:
        if abort_due_to_error:
            sys.stderr.write("Cleaning up after error...\n")
        if not release_done:
            jtagobj.reset(1, 1)                         # reset and release target
        if not options.no_close:
            jtagobj.close()                             # release communication port
        elif options.verbose:
            sys.stderr.write("WARNING: JTAG port is left open (--no-close)\n")

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise                                           # let pass exit() calls
    except KeyboardInterrupt:
        if DEBUG: raise                                 # show full trace in debug mode
        sys.stderr.write("User abort.\n")               # short messy in user mode
        sys.exit(1)                                     # set error level for script usage
    except Exception, msg:                              # every Exception is caught and displayed
        if DEBUG: raise                                 # show full trace in debug mode
        sys.stderr.write("\nAn error occurred:\n%s\n" % msg) # short messy in user mode
        sys.exit(1)                                     # set error level for script usage
