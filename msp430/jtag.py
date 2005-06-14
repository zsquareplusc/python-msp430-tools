# Parallel JTAG programmer for the MSP430 embedded proccessor.
#
# (C) 2002-2004 Chris Liechti <cliechti@gmx.net>
# this is distributed under a free software license, see license.txt
#
# http://mspgcc.sf.net
#
# Requires Python 2+ and the binary extension _parjtag or ctypes
# and MSP430mspgcc.dll/libMSP430mspgcc.so and HIL.dll/libHIL.so
#
# $Id: jtag.py,v 1.9 2005/06/14 10:15:26 cliechti Exp $

import sys

#erase modes
ERASE_SEGMENT = 0       #Erase a segment.
ERASE_MAIN    = 1       #Erase all MAIN memory.
ERASE_ALL     = 2       #Erase all MAIN and INFORMATION memory.

#Configurations of the MSP430 driver
VERIFICATION_MODE = 0   #Verify data downloaded to FLASH memories.
RAMSIZE_OPTION    = 1   #Change RAM used to download and program flash blocks
DEBUG_OPTION      = 2   #Set debug level. Enables debug outputs.
FLASH_CALLBACK    = 3   #Set a callback for progress report during flash write void f(WORD count, WORD total)

#reset methods
PUC_RESET = 1 << 0      #Power up clear (i.e., a "soft") reset.
RST_RESET = 1 << 1      #RST/NMI (i.e., "hard") reset.
VCC_RESET = 1 << 2      #Cycle Vcc (i.e., a "power on") reset.
ALL_RESETS = PUC_RESET + RST_RESET + VCC_RESET

DEBUG = 0

#exceptions
class JTAGException(Exception): pass

#1st try the ctypes implementation, if thats not available try to use the C extension
try:
    import ctypes
except ImportError:
    try:
        import _parjtag
    except ImportError:
        raise ImportError("Can't find neither _parjtag nor ctypes. No JTAG backend available.")
    else:
        backend = "_parjtag so/dll"
else:
    backend = "ctypes"
    
    STATUS_OK   = 0
    TRUE        = 1
    FALSE       = 0
    WRITE       = 0
    READ        = 1
    if sys.platform == 'win32':
        MSP430mspgcc = ctypes.windll.MSP430mspgcc
    else:
        MSP430mspgcc = ctypes.cdll.MSP430mspgcc
    
    MSP430_Initialize               = MSP430mspgcc.MSP430_Initialize
    MSP430_Initialize.argtypes      = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_long)]
    MSP430_Initialize.restype       = ctypes.c_int
    try:
        MSP430_Open                     = MSP430mspgcc.MSP430_Open
        MSP430_Open.argtypes            = []
        MSP430_Open.restype             = ctypes.c_int
    except AttributeError:
        if DEBUG:
            sys.stderr.write('MSP430_Open not found in library, using dummy.\n')
        #TI's USB-FET lib does not have this function
        def MSP430_Open():
            return STATUS_OK
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
    MSP430_Memory.argtypes          = [ctypes.c_long, ctypes.POINTER(ctypes.c_char), ctypes.c_long, ctypes.c_long]
    MSP430_Memory.restype           = ctypes.c_int
    MSP430_VerifyMem                = MSP430mspgcc.MSP430_VerifyMem
    MSP430_VerifyMem.argtypes       = [ctypes.c_long, ctypes.c_long, ctypes.c_char_p]
    MSP430_VerifyMem.restype        = ctypes.c_int
    MSP430_EraseCheck               = MSP430mspgcc.MSP430_EraseCheck
    MSP430_EraseCheck.argtypes      = ctypes.c_long, ctypes.c_long
    MSP430_EraseCheck.restype       = ctypes.c_int
    try:
        MSP430_ReadRegister             = MSP430mspgcc.MSP430_ReadRegister
        MSP430_ReadRegister.argtypes    = [ctypes.c_long, ctypes.POINTER(ctypes.c_long)]
        MSP430_ReadRegister.restype     = ctypes.c_int
        MSP430_WriteRegister            = MSP430mspgcc.MSP430_WriteRegister
        MSP430_WriteRegister.argtypes   = [ctypes.c_long, ctypes.c_long]
        MSP430_WriteRegister.restype    = ctypes.c_int
        MSP430_Funclet                  = MSP430mspgcc.MSP430_Funclet
        MSP430_Funclet.argtypes         = [ctypes.c_char_p, ctypes.c_long, ctypes.c_int, ctypes.c_int]
        MSP430_Funclet.restype          = ctypes.c_int
        MSP430_isHalted                 = MSP430mspgcc.MSP430_isHalted
        MSP430_isHalted.argtypes        = []
        MSP430_isHalted.restype         = ctypes.c_int
    except AttributeError:
        #TI's USB-FET lib does not have this function
        pass
    
    messagecallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_short, ctypes.c_short) #void f(WORD count, WORD total)

    class ParJTAG:
        """implementation of the _parjtag module in python with the help of ctypes"""
        
        def connect(self, port = None):
            """Enable JTAG and connect to target. This stops it.
            This function must be called before using any other JTAG function,
            or the other functions will yield unpredictable data."""
            version = ctypes.c_long()
            if port is None:
                if sys.platform == 'win32':
                    port = "1"
                else:
                    port = "/dev/parport0"
        
            status = MSP430_Initialize(port, ctypes.byref(version))
            if status != STATUS_OK:
                raise IOError("Could not initialize the library (port: %s)" % port)
        
            MSP430_VCC(3)
            
            status = MSP430_Open()
            if status != STATUS_OK:
                raise IOError("Can't open interface")
        
            status = MSP430_Configure(VERIFICATION_MODE, TRUE)
            if status != STATUS_OK:
                raise IOError("Could not configure the library")

        def release(self):
            """Release the target, disable JTAG lines.
            Subsequent access to the JTAG yields wrong data, until
            connect() is called again.
            The execution is started wherever the PC stays. Don't use this
            function after Flash operations or memverify. The PC was modified
            and points to an unpredicatble location. Use reset() before calling
            this function."""
            status = MSP430_Close(TRUE)
            if status != STATUS_OK:
                raise IOError("Could not close the library")
        
        def reset(self, execute = 0, release = 0, resets = ALL_RESETS):
            """Reset the device, optionaly start execution and/or release JTAG."""
            status = MSP430_Reset(resets, execute, release)
            if status != STATUS_OK:
                raise IOError("Could not reset target (no connection?)")

        def memread(self, address, size):
            """Read 'size' bytes starting at the specified address.
            The return value is a string with the (binary) data.
            It is possible to read peripherals, RAM as well as Flash."""
            buffer = (ctypes.c_char*(size))();
            
            status = MSP430_Memory(address, buffer, size, READ)
            if status == STATUS_OK:
                return ''.join([str(x) for x in buffer])
            else:
                raise IOError("Could not read target memory")

        def memwrite(self, address, buffer):
            """'mem' has to be a string, containing the data to write.
            It is possible to write peripherals, RAM as well as Flash.
            Flash must be erased before writing it with memerase()."""
            size = len(buffer)
            c_buffer = (ctypes.c_char*(size+2))();    #just to be sure + 2 (shouldn't be needed though)
            for i in range(size): c_buffer[i] = buffer[i]
            status = MSP430_Memory(address, c_buffer, size, WRITE)
            if status != STATUS_OK:
                raise IOError("Could not write target memory")

        def memverify(self, address, buffer):
            """'mem' has to be a string of even length.
            Verify device memory aginst the supplied data using PSA analysis."""
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
            segement must be specified. The length can be choosen larger than
            one segment to erase a consecutive block of segments.
            The erased segments are checked for erasure using PSA analysis."""
            status = MSP430_Erase(type, address, length)
            if status != STATUS_OK:
                raise IOError("Could not erase the Flash")

        def funclet(self, code):
            """Download a 'funclet' contained in the string 'code' to the target
            and execute it. This function waits until the code stops on a "jmp $"
            or a timeout.
            Please refer to the 'funclet' documentation for the contents of the
            code string."""
            size = len(code)
            if size & 1:
                raise ValueError("data must be of even size")
            
            status = MSP430_Funclet(code, size, 1, 1)
            if status != STATUS_OK:
                raise IOError("Could not execute code")

        def configure(self, mode, value = 0):
            """Configure the MSP430 driver."""
            status = MSP430_Configure(mode, value)
            if status != STATUS_OK:
                raise IOError("Could not change mode")

        def regread(self, regnum):
            """returns register value"""
            value = ctypes.c_long()
            status = MSP430_ReadRegister(regnum, ctypes.byref(value))
            if status != STATUS_OK:
                raise IOError("Could not read register")
            return value.value

        def regwrite(self, regnum, value):
            """write value to register"""
            status = MSP430_WriteRegister(regnum, value);
            if status != STATUS_OK:
                raise IOError("Could not write register")

        def set_flash_callback(self, function):
            """The 'function' is called with (count, total) as arguments
            while the flash is written."""

            self._callback = messagecallback(function)
            #~ MSP430_Configure(FLASH_CALLBACK, ctypes.addressof(self._callback))
            #hack following, close your eyes ;-)...
            argtypes = MSP430_Configure.argtypes
            MSP430_Configure.argtypes = [ctypes.c_long, messagecallback]
            MSP430_Configure(FLASH_CALLBACK, self._callback)
            MSP430_Configure.argtypes = argtypes

        def isHalted(self):
            """Check if cpu is stuck on an address."""
            value = MSP430_isHalted()
            return value
    
    _parjtag = ParJTAG()


class JTAG:
    """wrap the _parjtag extension.
    The action* methods all do output messages on stderr and they take their
    settings and data from the object and not as parameters.
    """

    def __init__(self):
        self.showprogess = 0
        self.data = None
        self.verbose = 1
    
    # ---------- direct use API ---------------
    
    def connect(self, lpt=None):
        """Connect to devcice at specified port, default = LPT1."""
        if lpt is None:
            _parjtag.connect()
        else:
            _parjtag.connect(lpt)

    def close(self):
        """Release device from JTAG"""
        _parjtag.release()

    def setDebugLevel(self, level):
        """Set level of debuggig messages."""
        global DEBUG
        DEBUG = level
        _parjtag.configure(DEBUG_OPTION, level)

    def setRamsize(self, ramsize):
        """Set download chunk size"""
        if DEBUG > 1: sys.stderr.write("* setRamsize(%d)\n" % ramsize)
        _parjtag.configure(RAMSIZE_OPTION, ramsize)

    def uploadData(self, startaddress, size):
        """Upload a datablock."""
        if DEBUG > 1: sys.stderr.write("* uploadData()\n")
        return _parjtag.memread(startaddress, size)

    def reset(self, execute=0, release=0):
        """perform a reset and optionaly release device."""
        if self.verbose:
            sys.stderr.write("Reset %sdevice...\n" % (release and 'and release ' or ''))
            sys.stderr.flush()
        _parjtag.reset(execute, release)

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
            def __init__(self, segaddr):
                self.address = segaddr
            def __call__(self):
                if self.verbose:
                    sys.stderr.write("Erase Segment @ 0x%04x...\n" % self.address)
                    sys.stderr.flush()
                _parjtag.memerase(ERASE_SEGMENT, self.address)
            def __repr__(self):
                return "Erase Segment @ 0x%04x" % self.address
        return SegmentEraser(address)

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
        """Textual progress output. Override in subclass to implement a different output"""
        sys.stderr.write("\r%d%%" % (100*count/total))
        sys.stderr.flush()

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
                _parjtag.memwrite(seg.startaddress, seg.data)
                bytes += len(seg.data)
            if self.verbose:
                sys.stderr.write("%i bytes programmed.\n" % bytes)
                sys.stderr.flush()
        else:
            raise JTAGException("Programming without data is not possible")

    def actionVerify(self):
        """Verify programmed data"""
        if self.data is not None:
            sys.stderr.write("Verify...\n")
            sys.stderr.flush()
            for seg in self.data:
                data = _parjtag.memread(seg.startaddress, len(seg.data))
                if data != seg.data: raise JTAGException("Verify failed")
        else:
            raise JTAGException("Verify without data not possible")

    def actionRun(self, address):
        """Start program at specified address"""
        raise NotImplementedError
        #sys.stderr.write("Load PC with 0x%04x ...\n" % address)

    def actionFunclet(self):
        """Download and start funclet"""
        if self.data is not None:
            if self.verbose:
                sys.stderr.write("Download and execute funclet...\n")
                sys.stderr.flush()
            if len(self.data) != 1:
                raise JTAGException("Funclets must have exactly one segment")
            _parjtag.funclet(self.data[0].data)
            if self.verbose:
                sys.stderr.write("Funclet OK.\n")
                sys.stderr.flush()
        else:
            raise JTAGException("No funclet available, set data")
