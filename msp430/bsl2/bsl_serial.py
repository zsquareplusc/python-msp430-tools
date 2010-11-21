"""
Simple MSP430 BSL implementation using the serial port.
"""

import bsl
import serial
import struct
import logging
import logging.config
import time

F1x_baudrate_args = {
     9600:[0x8580, 0x0000],
    19200:[0x86e0, 0x0001],
    38400:[0x87e0, 0x0002],
    57600:[0x0000, 0x0003],     #nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     #nonstandard XXX BSL dummy BCSCTL settings!
}
F2x_baudrate_args = {
     9600:[0x8880, 0x0000],
    19200:[0x8b00, 0x0001],
    38400:[0x8c80, 0x0002],
}
F4x_baudrate_args = {
     9600:[0x9800, 0x0000],
    19200:[0xb000, 0x0001],
    38400:[0xc800, 0x0002],
    57600:[0x0000, 0x0003],     #nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     #nonstandard XXX BSL dummy BCSCTL settings!
}

class SerialBSL(bsl.BSL):

    def __init__(self, port=0, baudrate=9600, ignore_answer=False):
        self.serial = None
        self.ignore_answer = ignore_answer
        self.extra_timeout = None
        self.logger = logging.getLogger('BSL')
        self.logger.info('Opening serial port %r' % port)
        try:
            self.serial = serial.serial_for_url(
                port,
                baudrate=baudrate,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_TWO,
                timeout=1,
            )
        except AttributeError:  # old PySerial versions do not have serial_for_url
            self.serial = serial.Serial(
                port,
                baudrate=baudrate,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_TWO,
                timeout=1,
            )
        self.invertRST = False
        self.invertTEST = False
        self.swapResetTest = False
        self.testOnTX = False
        self.blindWrite = False
        # delay after control line changes
        self.control_delay = 0.05

    def __del__(self):
        self.close()

    def close(self):
        self.logger.info('closing serial port')
        if self.serial is not None:
            self.serial.close()
            self.serial = None

    def sync(self):
        """send the sync character and wait for an acknowledge.
           the sync procedure is retried if it fails once or twice.
        """
        self.logger.debug('Sync...')
        if self.blindWrite:
            self.serial.write(bsl.BSL_SYNC)
            time.sleep(0.030)
        else:
            for tries in "210":
                self.serial.flushInput()
                self.serial.write(bsl.BSL_SYNC)
                ack = self.serial.read(1)
                if ack == bsl.DATA_ACK:
                    self.logger.debug('Sync OK')
                    return
                else:
                    if tries != '0':
                        self.logger.debug('Sync failed, retry...')
                    #if something was received, ensure that a small delay is made
                    if ack:
                        time.sleep(0.2)
            self.logger.error('Sync failed, aborting...')
            raise bsl.BSLTimeout("could not sync")

    def bsl(self, cmd, message='', expect=None):
        """\
        Lowlevel access to the serial communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer (an empty string for simple DATA_ACKs). In case of a failure
        read timeout or rejected commands by the slave, it will raise an
        exception.

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, DATA_ACK and DATA_FRAME are accepted and the
        answer is just returned.

        Frame format:
        +-----+-----+----+----+-----------+----+----+
        | HDR | CMD | L1 | L2 | D1 ... DN | CL | CH |
        +-----+-----+----+----+-----------+----+----+
        """
        self.logger.info('Command 0x%02x %r' % (cmd, message))
        #first synchronize with slave
        self.sync()
        #prepare command with checksum
        txdata = struct.pack('<cBBB', bsl.DATA_FRAME, cmd, len(message), len(message)) + message
        txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   #append checksum
        #~ self.logger.debug('Sending command: %r' % (txdata,))
        #transmit command
        self.serial.write(txdata)
        #wait for command answer
        if self.blindWrite:
            time.sleep(0.100)
            return
        if self.ignore_answer:
            return
        self.logger.debug('Reading answer...')
        if self.extra_timeout is None:
            ans = self.serial.read(1)
        else:
            for timeout in range(self.extra_timeout):
                ans = self.serial.read(1)
                if ans:
                    break
        #depending on answer type, read more, raise exceptions etc.
        if ans == '':
            raise bsl.BSLTimeout("timeout while reading answer (ack)")
        elif ans == bsl.DATA_NAK:
            self.logger.debug('Command failed (DATA_NAK)')
            raise bsl.BSLError("command failed (DATA_NAK)")
        elif ans == bsl.CMD_FAILED:
            self.logger.debug('Command failed (CMD_FAILED)')
            raise bsl.BSLError("command failed (CMD_FAILED)")
        elif ans == bsl.DATA_ACK:
            self.logger.debug('Simple ACK')
            if expect is not None and expect > 0:
                raise bsl.BSLError("expected data, but received a simple ACK")
            return ''
        elif ans == bsl.DATA_FRAME:
            self.logger.debug('Data frame...')
            head = self.serial.read(3)
            if len(head) != 3:
                raise BSLTimeout("timeout while reading answer (header)")
            (self.dummy, l1, l2) = struct.unpack('<BBB', head)
            if l1 != l2:
                raise bsl.BSLError("broken answer (L1 != L2)")
            if l1:
                data = self.serial.read(l1)
                if len(data) != l1:
                    raise bsl.BSLTimeout("timeout while reading answer (data)")
            else:
                data = ''
            checksum = self.serial.read(2)
            if len(checksum) != 2:
                raise bsl.BSLTimeout("timeout while reading answer (checksum)")
            if self.checksum(ans + head + data) ^ 0xffff == struct.unpack("<H", checksum)[0]:
                if expect is not None and len(data) != expect:
                    raise bsl.BSLError("expected %d bytes, got %d bytes" % (expect, len(data)))
                return data
            else:
                raise bsl.BSLException("checksum error in answer")
        else:
            self.logger.debug('unexpected answer %r' % (ans,))
            raise bsl.BSLError("unexpected answer: %r" % (ans,))

    def set_RST(self, level=1):
        """Controls RST/NMI pin (0: GND; 1: VCC; unless inverted flag is set)"""
        # invert signal if configured
        if self.invertRST:
            level = not level
        # set pin level
        if self.swapResetTest:
            self.serial.setRTS(level)
        else:
            self.serial.setDTR(level)
        time.sleep(self.control_delay)

    def set_TEST(self, level=1):
        """Controls TEST pin (inverted on board: 0: VCC; 1: GND; unless inverted flag is set)"""
        # invert signal if configured
        if self.invertTEST:
            level = not level
        #set pin level
        if self.swapResetTest:
            self.serial.setDTR(level)
        else:
            self.serial.setRTS(level)
        # make TEST signal on TX pin, unsing break condition.
        # currently only working on win32!
        if self.testOnTX:
            if level:
                serial.win32file.ClearCommBreak(self.serial.hComPort)
            else:
                serial.win32file.SetCommBreak(self.serial.hComPort)
        time.sleep(self.control_delay)

    def set_baudrate(self, baudrate):
        v = self.version()
        if v[0] == '\xf4':
            table = F4x_baudrate_args
        elif v[0] == '\xf2':
            table = F2x_baudrate_args
        else:
            table = F1x_baudrate_args
        self.logger.info('changing baudrate to %s' % baudrate)
        try:
            a, l = table[baudrate]
        except:
            raise ValueError('unsupported baudrate %s' % (baudrate,))
        else:
            self.BSL_CHANGEBAUD(a, l)
            self.serial.baudrate = baudrate

    def start_bsl(self):
        self.logger.info('ROM-BSL start pulse pattern')
        self.set_RST(1)         # power suply
        self.set_TEST(1)        # power suply
        time.sleep(0.250)       # charge capacitor on boot loader hardware

        self.set_RST(0)         # RST  pin: GND
        self.set_TEST(1)        # TEST pin: GND
        self.set_TEST(0)        # TEST pin: Vcc
        self.set_TEST(1)        # TEST pin: GND
        self.set_TEST(0)        # TEST pin: Vcc
        self.set_RST (1)        # RST  pin: Vcc
        self.set_TEST(1)        # TEST pin: GND
        time.sleep(0.250)       # give MSP430's oscillator time to stabilize

        self.serial.flushInput()    #clear buffers


if __name__ == '__main__':
    #~ logging.config.fileConfig('logger.ini')

    import sys
    import mspgcc.memory
    import mspgcc.util
    import optparse
    from copy import copy

    def check_address(option, opt, value):
        try:
            return int(value, 0)
        except ValueError:
            raise optparse.OptionValueError(
                "option %s: invalid address: %r" % (opt, value))

    class MyOption(optparse.Option):
        TYPES = optparse.Option.TYPES + ("address",)
        TYPE_CHECKER = copy(optparse.Option.TYPE_CHECKER)
        TYPE_CHECKER["address"] = check_address

    parser = optparse.OptionParser(option_class=MyOption, usage="%prog [options] file.a43")

    parser.add_option("-p", "--port", dest="port",
        help="Use com-port", default=0)
    parser.add_option("",   "--invert-test", dest="invert_test", action="store_true",
        help="invert RTS line", default=False)
    parser.add_option("",   "--invert-reset", dest="invert_reset", action="store_true",
        help="invert DTR line", default=False)

    parser.add_option("",   "--no-start", dest="start_pattern", action="store_false",
        help="no not use ROM-BSL start pattern on RST+TEST/TCK", default=True)
    parser.add_option("-s", "--speed", dest="speed", type=int,
        help="change baudrate (default 9600)", default=None)

    parser.add_option("-e", "--erase", dest="erase", action="store_true",
        help="erase flash memory", default=False)

    parser.add_option("", "--upload", dest="upload", action="store", type="address",
        help="memory read, see also --size", default=None)
    parser.add_option("", "--size", dest="size", action="store", type="address",
        help="see also --upload", default=512)
    parser.add_option("--passwd", dest="passwd", action="store",
        help="transmit password before doing anything else", default=None)
    parser.add_option("--ignore-answer", dest="ignore_answer", action="store_true",
        help="do not wait for answer", default=False)
    parser.add_option("--control-delay", dest="control_delay", type="float",
        help="Set delay in seconds (float) for BSL start pattern", default=0.05)

    parser.add_option("", "--time", dest="time", action="store_true",
        help="measure time", default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
        help="print progress messages", default=False)

    (options, args) = parser.parse_args()

    #instantiate BSL communication object
    target = SerialBSL(
        options.port,
        ignore_answer = options.ignore_answer,
    )

    target.control_delay = options.control_delay

    if options.verbose:
        logging.basicConfig()
        logger = logging.getLogger('BSL')
        logger.setLevel(logging.DEBUG)

    if options.invert_test:
        target.invertTEST = True
        target.set_TEST(1)

    if options.invert_reset:
        target.invertRST= True
        target.set_RST(1)

    if options.time:
        start_time = time.time()

    if options.start_pattern:
        target.start_bsl()

    if options.erase:
        target.extra_timeout = 6
        target.mass_erase()
        target.extra_timeout = None
        target.BSL_TXPWORD("\xff"*32)
    else:
        if options.passwd is not None:
            target.BSL_TXPWORD(options.passwd)

    if options.speed is not None:
        target.set_baudrate(options.speed)

    # if upload, do it and exit
    if options.upload is not None:
        mspgcc.util.hexdump((options.upload, target.memory_read(options.upload, options.size)))
        sys.exit(0)

    if args:
        #else download firmware, error if no file is given
        if len(args) != 1:
            parser.error("expecting one firmware file name")

        application = mspgcc.memory.Memory()
        application.loadFile(args[0])

        for segment in application:
            if len(segment.data) & 1:
                segment.data += '\xff'
            target.memory_write(segment.startaddress, segment.data)
            verify = target.memory_read(segment.startaddress, len(segment.data))
            if verify != segment.data:
                raise Exception("write segment at 0x%04x failed" % segment.startaddress)
        target.reset()
        if options.verbose: logging.info("Done")

    if options.time:
        end_time = time.time()
        print "Time: %.1f s" % (end_time - start_time)
