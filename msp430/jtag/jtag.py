#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2002-2012 Chris Liechti <cliechti@gmx.net>
# All Rights Reserved.
# Simplified BSD License (see LICENSE.txt for full text)

"""\
JTAG programmer for the TI MSP430 embedded processor.

Requires Python 2+, ctypes and MSP430mspgcc.dll/libMSP430mspgcc.so or
MSP430.dll/libMSP430.so and HIL.dll/libHIL.so
"""

import sys
import os
import ctypes

# erase modes
ERASE_SEGMENT = 0       # Erase a segment.
ERASE_MAIN    = 1       # Erase all MAIN memory.
ERASE_ALL     = 2       # Erase all MAIN and INFORMATION memory.

# Configurations of the MSP430 driver
# TI and MSPGCC's library
VERIFICATION_MODE = 0   # Verify data downloaded to FLASH memories.
# MSPGCC's library
RAMSIZE_OPTION    = 1   # Change RAM used to download and program flash blocks
DEBUG_OPTION      = 2   # Set debug level. Enables debug outputs.
FLASH_CALLBACK    = 3   # Set a callback for progress report during flash write void f(WORD count, WORD total)
# TI's library
EMULATION_MODE  = 1
CLK_CNTRL_MODE  = 2
MCLK_CNTRL_MODE = 3
FLASH_TEST_MODE = 4     # Flash Marginal Read Test.
LOCKED_FLASH_ACCESS = 5 # Allows Locked Info Mem Segment A access (if set to '1')
FLASH_SWOP = 6
EDT_TRACE_MODE = 7
INTERFACE_MODE = 8      # see INTERFACE_TYPE below
SET_MDB_BEFORE_RUN = 9
RAM_PRESERVE_MODE = 10  # Configure whether RAM content should be preserved/restored

# INTERFACE_TYPE
JTAG_IF = 0
SPYBIWIRE_IF = 1
SPYBIWIREJTAG_IF = 2
AUTOMATIC_IF = 3

# FLASH_TEST_MODE
FLASH_MARGINAL_READ_OFF = 0
FLASH_MARGINAL_READ_0 = 1
FLASH_MARGINAL_READ_1 = 2

# reset methods
PUC_RESET = 1 << 0      # Power up clear (i.e., a "soft") reset.
RST_RESET = 1 << 1      # RST/NMI (i.e., "hard") reset.
VCC_RESET = 1 << 2      # Cycle Vcc (i.e., a "power on") reset.
ALL_RESETS = PUC_RESET + RST_RESET + VCC_RESET

# interface type 'spy-bi-wire' or 'JTAG'
interface = 'JTAG'

DEBUG = 0

# for module tests, enable debug outputs from the beginning on
if __name__ == '__main__':
    DEBUG = 1

# ctypes backend variations:
CTYPES_MSPGCC = "ctypes/mspgcc"
CTYPES_TI = "ctypes/TI or 3rd party"

# exceptions
class JTAGException(Exception): pass

def locate_library(libname, paths=sys.path, loader=None, verbose=0):
    if loader is None: loader=ctypes.windll
    for path in paths:
        if path.lower().endswith('.zip'):
            path = os.path.dirname(path)
        library = os.path.join(path, libname)
        if verbose > 4: sys.stderr.write('trying %r...\n' % library)
        if os.path.exists(library):
            if verbose > 4: sys.stderr.write('using %r\n' % library)
            return loader.LoadLibrary(library), library
    else:
        raise IOError('%s not found' % libname)

# create a wrapper class with ctypes, that has the same API as _parjtag
backend = None
backend_info = None
_parjtag = None

def init_backend(force=None, verbose=0):
    global backend
    global backend_info
    global _parjtag
    global search_path

    # an absolute path to the library can be given.
    # LIBMSPGCC_PATH is used to pass its location
    search_path = []
    # if environment variable is set, insert this path first
    try:
        search_path.insert(0, os.environ['LIBMSPGCC_PATH'])
    except KeyError:
        if verbose > 4: sys.stderr.write('LIBMSPGCC_PATH is not set\n')
        if sys.platform == 'win32':
            search_path.insert(0, os.path.abspath('.'))
            # as fallback, append PATH
            try:
                search_path.extend(os.environ['PATH'].split(os.pathsep))
            except KeyError:
                pass
        else:
            # as fallback, append PATH
            try:
                search_path.extend(os.environ['LD_LIBRARY_PATH'].split(os.pathsep))
            except KeyError:
                pass
    #~ print search_path

    STATUS_OK    = 0
    STATUS_ERROR = -1
    TRUE         = 1
    FALSE        = 0
    WRITE        = 0
    READ         = 1
    if sys.platform == 'win32':
        # the library is found on the PATH, respectively in the executables directory
        if force == CTYPES_MSPGCC:
            MSP430mspgcc, backend_info = locate_library('MSP430mspgcc.dll', search_path, verbose=verbose)
            backend = CTYPES_MSPGCC
        elif force == CTYPES_TI:
            #~ MSP430mspgcc = ctypes.windll.MSP430
            MSP430mspgcc, backend_info = locate_library('MSP430.dll', search_path, verbose=verbose)
            backend = CTYPES_TI
        elif force is None:
            # autodetect
            try:
                # try to use the TI or third party library
                MSP430mspgcc, backend_info = locate_library('MSP430.dll', search_path, verbose=verbose)
                backend = CTYPES_TI
            except IOError:
                # when that fails, use the mspgcc implementation
                MSP430mspgcc, backend_info = locate_library('MSP430mspgcc.dll', search_path, verbose=verbose)
                backend = CTYPES_MSPGCC
        else:
            raise ValueError("no such backend: %r" % force)
    else:
        # the library is found on the PATH, respectively in the executables directory
        try:
            if force == CTYPES_MSPGCC:
                MSP430mspgcc, backend_info = locate_library('libMSP430mspgcc.so', search_path, ctypes.cdll, verbose=verbose)
                backend = CTYPES_MSPGCC
            elif force == CTYPES_TI:
                #~ MSP430mspgcc = ctypes.windll.MSP430
                MSP430mspgcc, backend_info = locate_library('libMSP430.so', search_path, ctypes.cdll, verbose=verbose)
                backend = CTYPES_TI
            elif force is None:
                # autodetect
                try:
                    # try to use the TI or third party library
                    MSP430mspgcc, backend_info = locate_library('libMSP430.so', search_path, ctypes.cdll, verbose=verbose)
                    backend = CTYPES_TI
                except IOError:
                    # when that fails, use the mspgcc implementation
                    MSP430mspgcc, backend_info = locate_library('libMSP430mspgcc.so', search_path, ctypes.cdll, verbose=verbose)
                    backend = CTYPES_MSPGCC
            else:
                raise ValueError("no such backend: %r" % force)
        except IOError, e:
            raise IOError('The environment variable "LIBMSPGCC_PATH" must point to the folder that contains "libMSP430mspgcc.so" or "libMSP430.so": %s' % e)

    global MSP430_Initialize, MSP430_Open, MSP430_Identify, MSP430_Close
    global MSP430_Configure, MSP430_VCC, MSP430_Reset, MSP430_Erase
    global MSP430_Memory, MSP430_VerifyMem, MSP430_EraseCheck
    global MSP430_ReadRegister, MSP430_WriteRegister, MSP430_FuncletWait
    global MSP430_isHalted, MSP430_Error_Number, MSP430_Error_String
    global MSP430_Secure, MSP430_readMAB

    MSP430_Initialize               = MSP430mspgcc.MSP430_Initialize
    MSP430_Initialize.argtypes      = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_long)]
    MSP430_Initialize.restype       = ctypes.c_int
    if backend == CTYPES_MSPGCC:
        MSP430_Open                 = MSP430mspgcc.MSP430_Open
        MSP430_Open.argtypes        = []
        MSP430_Open.restype         = ctypes.c_int
    else:
        STATUS_T = ctypes.c_long
        MSP430_Identify             = MSP430mspgcc.MSP430_Identify
        MSP430_Identify.argtypes    = [ctypes.POINTER(ctypes.c_char*80), ctypes.c_long, ctypes.c_long]
        MSP430_Identify.restype     = ctypes.c_int
        # TI's USB-FET lib does not have this function, they have an MSP430_Identify instead
        def MSP430_Open():
            buffer = (ctypes.c_char*80)()
            status = MSP430_Identify(ctypes.byref(buffer), 80, 0)
            if status != STATUS_OK:
                return STATUS_ERROR
            if verbose:
                sys.stderr.write('MSP430_Identify: Device type: %r\n' % str(buffer[4:36]).replace('\0',''))
            #~ status = MSP430_Reset(ALL_RESETS, FALSE, FALSE)
            return status

        global MSP430_FET_FwUpdate
        MSP430_FET_FwUpdate             = MSP430mspgcc.MSP430_FET_FwUpdate
        MSP430_FET_FwUpdate.argtypes    = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_long] # filename, callback, handle
        MSP430_FET_FwUpdate.restype     = STATUS_T

    MSP430_Close                    = MSP430mspgcc.MSP430_Close
    MSP430_Close.argtypes           = [ctypes.c_long]
    MSP430_Close.restype            = ctypes.c_int
    MSP430_Configure                = MSP430mspgcc.MSP430_Configure
    MSP430_Configure.argtypes       = [ctypes.c_long, ctypes.c_long]
    MSP430_Configure.restype        = ctypes.c_int
    MSP430_VCC                      = MSP430mspgcc.MSP430_VCC
    MSP430_VCC.argtypes             = [ctypes.c_long]
    MSP430_VCC.restype              = ctypes.c_int
    MSP430_Reset                    = MSP430mspgcc.MSP430_Reset
    MSP430_Reset.argtypes           = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
    MSP430_Reset.restype            = ctypes.c_int
    MSP430_Erase                    = MSP430mspgcc.MSP430_Erase
    MSP430_Erase.argtypes           = [ctypes.c_long, ctypes.c_long, ctypes.c_long]
    MSP430_Erase.restype            = ctypes.c_int
    MSP430_Memory                   = MSP430mspgcc.MSP430_Memory
    MSP430_Memory.argtypes          = [ctypes.c_long, ctypes.POINTER(ctypes.c_uint8), ctypes.c_long, ctypes.c_long]
    MSP430_Memory.restype           = ctypes.c_int
    MSP430_VerifyMem                = MSP430mspgcc.MSP430_VerifyMem
    MSP430_VerifyMem.argtypes       = [ctypes.c_long, ctypes.c_long, ctypes.POINTER(ctypes.c_uint8)]
    MSP430_VerifyMem.restype        = ctypes.c_int
    MSP430_EraseCheck               = MSP430mspgcc.MSP430_EraseCheck
    MSP430_EraseCheck.argtypes      = ctypes.c_long, ctypes.c_long
    MSP430_EraseCheck.restype       = ctypes.c_int
    if backend == CTYPES_MSPGCC:
        MSP430_ReadRegister             = MSP430mspgcc.MSP430_ReadRegister
        MSP430_ReadRegister.argtypes    = [ctypes.c_long, ctypes.POINTER(ctypes.c_long)]
        MSP430_ReadRegister.restype     = ctypes.c_int
        MSP430_WriteRegister            = MSP430mspgcc.MSP430_WriteRegister
        MSP430_WriteRegister.argtypes   = [ctypes.c_long, ctypes.c_long]
        MSP430_WriteRegister.restype    = ctypes.c_int
    else:
        # TI's USB-FET lib does not have this function
        if verbose:
            sys.stderr.write('MSP430_*Register not found in library. Not supported.\n')
    if backend == CTYPES_MSPGCC:
        #~ MSP430_Funclet                  = MSP430mspgcc.MSP430_Funclet
        #~ MSP430_Funclet.argtypes         = [ctypes.c_char_p, ctypes.c_long, ctypes.c_int, ctypes.c_int]
        #~ MSP430_Funclet.restype          = ctypes.c_int
        MSP430_FuncletWait              = MSP430mspgcc.MSP430_FuncletWait
        MSP430_FuncletWait.argtypes     = [ctypes.c_char_p, ctypes.c_long, ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
        MSP430_FuncletWait.restype      = ctypes.c_int
        MSP430_isHalted                 = MSP430mspgcc.MSP430_isHalted
        MSP430_isHalted.argtypes        = []
        MSP430_isHalted.restype         = ctypes.c_int
    else:
        # TI's USB-FET lib does not have this function
        if verbose:
            sys.stderr.write('MSP430_Funclet and isHalted not found in library. Not supported.\n')
    MSP430_Error_Number             = MSP430mspgcc.MSP430_Error_Number
    MSP430_Error_Number.argtypes    = []
    MSP430_Error_Number.restype     = ctypes.c_long
    MSP430_Error_String             = MSP430mspgcc.MSP430_Error_String
    MSP430_Error_String.argtypes    = [ctypes.c_long]
    MSP430_Error_String.restype     = ctypes.c_char_p
    try:
        MSP430_Secure                   = MSP430mspgcc.MSP430_Secure
        MSP430_Secure.argtypes          = []
        MSP430_Secure.restype           = ctypes.c_int
    except AttributeError:
        # mspgcc lib does not have this function
        if verbose:
            sys.stderr.write('MSP430_Secure not found in library. Not supported.\n')
        def MSP430_Secure():
            raise NotImplementedError("this function is not supported with this MSP430 library")
    try:
        MSP430_readMAB                  = MSP430mspgcc.MSP430_readMAB
        MSP430_readMAB.argtypes         = []
        MSP430_readMAB.restype          = ctypes.c_int
    except AttributeError:
        pass

    messagecallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_ushort, ctypes.c_ushort) # void f(WORD count, WORD total)

    class MSP430Library(object):
        """implementation of the _parjtag module in python with the help of ctypes"""

        def open(self, port = None):
            """Initilize library"""
            version = ctypes.c_long(0)
            if port is None:
                if sys.platform == 'win32':
                    port = "1"
                else:
                    port = "/dev/parport0"
            if backend == CTYPES_TI and sys.platform == 'win32':
                port = port.upper()
            status = MSP430_Initialize(port, ctypes.byref(version))
            if status != STATUS_OK:
                raise IOError("Could not initialize the library (port: %s)" % port)
            if verbose:
                sys.stderr.write('backend library version: %d\n' % (version.value,))
            if version.value < 0:
                # warn if firmware and MSP430.dll are incompatible
                sys.stderr.write('WARNING: FET Firmware not compatible with MSP430 library!\n')
                sys.stderr.write('         Consider using --fet-update.\n')
            if backend == CTYPES_TI:
                if interface == 'spy-bi-wire':
                    status = MSP430_Configure(INTERFACE_MODE, SPYBIWIRE_IF)
                    if status != STATUS_OK:
                        raise IOError("Could not configure the library: %s (device not spi-bi-wire capable?)" % MSP430_Error_String(MSP430_Error_Number()))
                elif interface == 'spy-bi-wire-jtag':
                    status = MSP430_Configure(INTERFACE_MODE, SPYBIWIREJTAG_IF)
                    if status != STATUS_OK:
                        raise IOError("Could not configure the library: %s (device not spi-bi-wire capable?)" % MSP430_Error_String(MSP430_Error_Number()))
                else:
                    # try to use auto detection
                    status = MSP430_Configure(INTERFACE_MODE, AUTOMATIC_IF)
                    if status != STATUS_OK:
                        # fallback to 4 wire mode
                        status = MSP430_Configure(INTERFACE_MODE, JTAG_IF)
                        if status != STATUS_OK:
                            raise IOError("Could not configure the library: %s (spy-bi-wire device/connection?)" % MSP430_Error_String(MSP430_Error_Number()))
            else:
                if interface != 'JTAG':
                    raise ValueError("interface != 'JTAG' is not supported with this backend")

        def connect(self,):
            """Enable JTAG and connect to target. This stops it.
            This function must be called before using any other JTAG function,
            or the other functions will yield unpredictable data."""
            MSP430_VCC(3000)

            status = MSP430_Open()
            if status != STATUS_OK:
                raise IOError("Can't open interface: %s" % MSP430_Error_String(MSP430_Error_Number()))

            status = MSP430_Configure(VERIFICATION_MODE, TRUE)
            if status != STATUS_OK:
                raise IOError("Could not configure the library: %s" % MSP430_Error_String(MSP430_Error_Number()))
            if backend == CTYPES_TI:
                # switch off the RAM preserve mode, to speed up operations
                # it also makes the behaviour closer to mspgcc the library
                status = MSP430_Configure(RAM_PRESERVE_MODE, FALSE)
                if status != STATUS_OK:
                    raise IOError("Could not configure the library: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def release(self):
            """Release the target, disable JTAG lines.
            Subsequent access to the JTAG yields wrong data, until
            connect() is called again.
            The execution is started wherever the PC stays. Don't use this
            function after Flash operations or memverify. The PC was modified
            and points to an unpredictable location. Use reset() before calling
            this function."""
            status = MSP430_Close(TRUE)
            if status != STATUS_OK:
                raise IOError("Could not close the library: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def reset(self, execute = 0, release = 0, resets = ALL_RESETS):
            """Reset the device, optionaly start execution and/or release JTAG."""
            status = MSP430_Reset(resets, execute, release)
            if status != STATUS_OK:
                raise IOError("Could not reset target (no connection?): %s" % MSP430_Error_String(MSP430_Error_Number()))

        def memread(self, address, size):
            """Read 'size' bytes starting at the specified address.
            The return value is a string with the (binary) data.
            It is possible to read peripherals, RAM as well as Flash."""
            if size < 0: raise ValueError("Size must not be negative")
            buffer = (ctypes.c_uint8*size)();

            status = MSP430_Memory(address, buffer, size, READ)
            if status == STATUS_OK:
                return bytearray([x for x in buffer])
            else:
                raise IOError("Could not read target memory: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def memwrite(self, address, buffer):
            """'mem' has to be a string, containing the data to write.
            It is possible to write peripherals, RAM as well as Flash.
            Flash must be erased before writing it with memerase()."""
            if backend == CTYPES_TI:
                # we want to be able to write the locked segments
                status = MSP430_Configure(LOCKED_FLASH_ACCESS, 1)
                if status != STATUS_OK:
                    raise IOError("Could not configure the library: %s" % MSP430_Error_String(MSP430_Error_Number()))
            size = len(buffer)
            c_buffer = (ctypes.c_uint8*(size+2))();    # just to be sure + 2 (shouldn't be needed though)
            for i in range(size): c_buffer[i] = buffer[i]
            status = MSP430_Memory(address, c_buffer, size, WRITE)
            if status != STATUS_OK:
                raise IOError("Could not write target memory: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def memverify(self, address, buffer):
            """'mem' has to be a string of even length.
            Verify device memory against the supplied data using PSA analysis."""
            size = len(buffer)
            if size & 1:
                raise ValueError("Buffer must have an even length")
            status = MSP430_VerifyMem(address, size, buffer)
            return (status == STATUS_OK)

        def memerase(self, type=ERASE_ALL, address=0xfffe, length=2):
            """Erase the Flash.

            Valid modes are:
                ERASE_SEGMENT = 0
                ERASE_MAIN    = 1
                ERASE_ALL     = 2

            The default address and length is fine for mass and main erase.
            To erase a single segment ERASE_SEGMENT and an address within that
            segment must be specified. The length can be chosen larger than
            one segment to erase a consecutive block of segments.
            The erased segments are checked for erasure using PSA analysis."""
            if backend == CTYPES_TI:
                # we want to be able to write the locked segments
                status = MSP430_Configure(LOCKED_FLASH_ACCESS, type != ERASE_ALL)
                if status != STATUS_OK:
                    raise IOError("Could not configure the library: %s" % MSP430_Error_String(MSP430_Error_Number()))
            status = MSP430_Erase(type, address, length)
            if status != STATUS_OK:
                raise IOError("Could not erase the Flash: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def funclet(self, code, timeout=1000):
            """Download a 'funclet' contained in the string 'code' to the target
            and execute it. This function waits until the code stops on a "jmp $"
            or a timeout.
            Please refer to the 'funclet' documentation for the contents of the
            code string.
            return the runtime in seconds"""
            runtime = ctypes.c_ulong()
            size = len(code)
            if size & 1:
                raise ValueError("data must be of even size")

            status = MSP430_FuncletWait(code, size, 1, timeout, ctypes.byref(runtime))
            if status != STATUS_OK:
                raise IOError("Could not execute code: %s" % MSP430_Error_String(MSP430_Error_Number()))
            return runtime.value

        def configure(self, mode, value = 0):
            """Configure the MSP430 driver."""
            status = MSP430_Configure(mode, value)
            if status != STATUS_OK:
                raise IOError("Could not change mode: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def regread(self, regnum):
            """returns register value"""
            value = ctypes.c_long()
            status = MSP430_ReadRegister(regnum, ctypes.byref(value))
            if status != STATUS_OK:
                raise IOError("Could not read register: %s" % MSP430_Error_String(MSP430_Error_Number()))
            return value.value

        def regwrite(self, regnum, value):
            """write value to register"""
            status = MSP430_WriteRegister(regnum, value);
            if status != STATUS_OK:
                raise IOError("Could not write register: %s" % MSP430_Error_String(MSP430_Error_Number()))

        def set_flash_callback(self, function):
            """The 'function' is called with (count, total) as arguments
            while the flash is written."""
            if backend == CTYPES_MSPGCC:
                self._callback = messagecallback(function)
                #~ MSP430_Configure(FLASH_CALLBACK, ctypes.addressof(self._callback))
                # hack following, close your eyes ;-)...
                argtypes = MSP430_Configure.argtypes
                MSP430_Configure.argtypes = [ctypes.c_long, messagecallback]
                MSP430_Configure(FLASH_CALLBACK, self._callback)
                MSP430_Configure.argtypes = argtypes
            else:
                raise JTAGException("callbacks are not supported with other libraries than mspgcc's")

        def isHalted(self):
            """Check if cpu is stuck on an address."""
            value = MSP430_isHalted()
            return value

        def secure(self):
            """burn JTAG security fuse.
               Note: not reversibly. use with care.
               Note: not supported by all JTAG adapters.
            """
            status = MSP430_Secure()
            if status != STATUS_OK:
                raise IOError("Could not secure device: %s" % MSP430_Error_String(MSP430_Error_Number()))

    _parjtag = MSP430Library()

    # print the used backend
    if verbose:
        sys.stderr.write("JTAG backend: %s (%s)\n" % (backend, backend_info))
        #~ if backend == CTYPES_MSPGCC:
            #~ _parjtag.configure(DEBUG_OPTION, verbose)


class JTAG(object):
    """\
    Wrap the MSP430Library object.

    The action* methods all do output messages on stderr and they take their
    settings and data from the object and not as parameters.
    """

    def __init__(self):
        self.showprogess = 0
        self.data = None
        self.verbose = 1

    # ---------- direct use API ---------------

    def open(self, lpt=None):
        """Initialize and open port."""
        if backend is None: init_backend()
        if lpt is None:
            _parjtag.open()
        else:
            _parjtag.open(lpt)

    def connect(self):
        """Connect to device."""
        _parjtag.connect()

    def close(self):
        """Release device from JTAG."""
        if _parjtag is not None:
            _parjtag.release()

    def setDebugLevel(self, level):
        """Set level of debugging messages."""
        global DEBUG
        DEBUG = level
        #~ self.verbose = level
        # this option is only available in the mspgcc library
        if backend == CTYPES_MSPGCC:
            _parjtag.configure(DEBUG_OPTION, level)

    def setRamsize(self, ramsize):
        """Set download chunk size."""
        if DEBUG > 1: sys.stderr.write("* setRamsize(%d)\n" % ramsize)
        # this option is only available in the mspgcc library
        if backend == CTYPES_MSPGCC:
            _parjtag.configure(RAMSIZE_OPTION, ramsize)
        else:
            if DEBUG > 1: sys.stderr.write("* setRamsize ignored for %s backend\n" % backend)

    def downloadData(self, startaddress, data):
        """Write data to given address."""
        _parjtag.memwrite(startaddress, data)

    def uploadData(self, startaddress, size):
        """Upload a datablock."""
        if DEBUG > 1: sys.stderr.write("* uploadData()\n")
        return _parjtag.memread(startaddress, size)

    def reset(self, execute=0, release=0):
        """Perform a reset and optionally release device."""
        if self.verbose:
            sys.stderr.write("Reset %sdevice...\n" % (release and 'and release ' or ''))
            sys.stderr.flush()
        if _parjtag is not None:
            _parjtag.reset(execute, release)
        #~ _parjtag.reset(execute, release, PUC_RESET + RST_RESET)

    def getCPURegister(self, regnum):
        """Read CPU register."""
        return _parjtag.regread(regnum)

    def setCPURegister(self, regnum, value):
        """Write CPU register."""
        _parjtag.regwrite(regnum, value)

    # ---------- action based API ---------------

    def actionMassErase(self):
        """Erase the flash memory completely (with mass erase command)."""
        if self.verbose:
            sys.stderr.write("Mass Erase...\n")
        _parjtag.memerase(ERASE_ALL)

    def actionMainErase(self):
        """Erase the MAIN flash memory, leave the INFO mem"""
        if self.verbose:
            sys.stderr.write("Erase Main Flash...\n")
            sys.stderr.flush()
        _parjtag.memerase(ERASE_MAIN, 0xfffe)

    def makeActionSegmentErase(self, address):
        """Selective segment erase, the returned object can be called
        to execute the action."""
        class SegmentEraser:
            def __init__(self, segaddr, verbose=0):
                self.address = segaddr
                self.verbose = verbose
            def __call__(self):
                if self.verbose:
                    sys.stderr.write("Erase Segment @ 0x%04x...\n" % self.address)
                    sys.stderr.flush()
                _parjtag.memerase(ERASE_SEGMENT, self.address)
            def __repr__(self):
                return "Erase Segment @ 0x%04x" % self.address
        return SegmentEraser(address, self.verbose)

    def actionEraseCheck(self):
        """Check the erasure of required flash cells. Erase check by file."""
        sys.stderr.write("Erase Check by file...\n")
        if self.data is not None:
            for seg in self.data:
                data = _parjtag.memread(seg.startaddress, len(seg.data))
                if data != '\xff'*len(seg.data): raise JTAGException("Erase check failed")
        else:
            raise JTAGException("Cannot do erase check against data with not knowing the actual data")

    def progess_update(self, count, total):
        """Textual progress output. Override in subclass to implement a
        different output."""
        sys.stderr.write("\r%d%%" % (100*count/total))
        sys.stderr.flush()
        return 0

    def actionProgram(self):
        """Program data into flash memory."""
        if self.data is not None:
            if self.verbose:
                sys.stderr.write("Program...\n")
                sys.stderr.flush()
            if self.showprogess:
                _parjtag.set_flash_callback(self.progess_update)
            bytes = 0
            for seg in self.data:
                # pad length if it is not even
                if len(seg.data) & 1: seg.data += '\xff'
                _parjtag.memwrite(seg.startaddress, seg.data)
                bytes += len(seg.data)
            if self.verbose:
                sys.stderr.write("%i bytes programmed.\n" % bytes)
                sys.stderr.flush()
        else:
            raise JTAGException("Programming without data is not possible")

    def actionVerify(self):
        """Verify programmed data."""
        if self.data is not None:
            sys.stderr.write("Verify...\n")
            sys.stderr.flush()
            for seg in self.data:
                data = _parjtag.memread(seg.startaddress, len(seg.data))
                if data != seg.data: raise JTAGException("Verify failed")
        else:
            raise JTAGException("Verify without data not possible")

    def actionRun(self, address):
        """Start program at specified address."""
        raise NotImplementedError("actionRun not supported")
        #sys.stderr.write("Load PC with 0x%04x ...\n" % address)

    def actionFunclet(self, timeout=1):
        """Download and start funclet. Timeout in seconds."""
        if self.data is not None:
            if self.verbose:
                sys.stderr.write("Download and execute funclet...\n")
                sys.stderr.flush()
            if len(self.data) != 1:
                raise JTAGException("Funclets must have exactly one segment")
            runtime = _parjtag.funclet(self.data[0].data, int(timeout*1000)) / 1000.0
            if runtime >= timeout:
                sys.stderr.write("Funclet stopped on timeout\n")
                sys.stderr.flush()
            if self.verbose:
                sys.stderr.write("Funclet OK (%.2fs).\n" % (runtime,))
                sys.stderr.flush()
        else:
            raise JTAGException("No funclet available, set data")

    def actionSecure(self):
        """Secure device by burning the JTAG security fuse."""
        if self.verbose:
            sys.stderr.write("Blowing JTAG fuse...\n")
            sys.stderr.flush()
        _parjtag.secure()


# simple, stupid module test, debug is set above
if __name__ == '__main__':
    #~ init_backend(CTYPES_MSPGCC)
    #~ init_backend(CTYPES_TI)
    jtagobj = JTAG()
    print "Backend: %s" % (backend, )
    jtagobj.open()
    try:
        jtagobj.connect()
        jtagobj.reset()
    finally:
        jtagobj.close()
