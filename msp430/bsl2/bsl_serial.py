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
    57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
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
    57600:[0x0000, 0x0003],     # nonstandard XXX BSL dummy BCSCTL settings!
   115200:[0x0000, 0x0004],     # nonstandard XXX BSL dummy BCSCTL settings!
}

class SerialBSL(bsl.BSL):

    def __init__(self):
        self.serial = None
        self.logger = logging.getLogger('BSL')
        self.extra_timeout = None
        self.invertRST = False
        self.invertTEST = False
        self.swapResetTest = False
        self.testOnTX = False
        self.blindWrite = False
        # delay after control line changes
        self.control_delay = 0.05

    def open(self, port=0, baudrate=9600, ignore_answer=False):
        self.ignore_answer = ignore_answer
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
                    # if something was received, ensure that a small delay is made
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
        # first synchronize with slave
        self.sync()
        # prepare command with checksum
        txdata = struct.pack('<cBBB', bsl.DATA_FRAME, cmd, len(message), len(message)) + message
        txdata += struct.pack('<H', self.checksum(txdata) ^ 0xffff)   #append checksum
        #~ self.logger.debug('Sending command: %r' % (txdata,))
        # transmit command
        self.serial.write(txdata)
        # wait for command answer
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
        # depending on answer type, read more, raise exceptions etc.
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
        # set pin level
        if self.swapResetTest:
            self.serial.setDTR(level)
        else:
            self.serial.setRTS(level)
        # make TEST signal on TX pin, unsing break condition.
        if self.testOnTX:
            self.serial.setBreak(level)
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

    import msp430.target
    from optparse import OptionGroup
    import sys
    import msp430.memory
    import optparse

    class SerialBSLTarget(SerialBSL, msp430.target.Target):
        def __init__(self):
            msp430.target.Target.__init__(self)
            SerialBSL.__init__(self)

        def add_extra_options(self):
            group = OptionGroup(self.parser, "Communication settings")

            group.add_option("-p", "--port",
                    dest="port",
                    help="Use com-port",
                    default=0)
            group.add_option("--invert-test",
                    dest="invert_test",
                    action="store_true",
                    help="invert RTS line",
                    default=False)
            group.add_option("--invert-reset",
                    dest="invert_reset",
                    action="store_true",
                    help="invert DTR line",
                    default=False)

            self.parser.add_option_group(group)


            group = OptionGroup(self.parser, "BSL settings")

            group.add_option("--no-start",
                    dest="start_pattern",
                    action="store_false",
                    help="no not use ROM-BSL start pattern on RST+TEST/TCK",
                    default=True)

            group.add_option("-s", "--speed",
                    dest="speed",
                    type=int,
                    help="change baudrate (default 9600)",
                    default=None)

            self.parser.add_option("--password",
                    dest="password",
                    action="store",
                    help="transmit password before doing anything else, password is given in given (TI-Text/ihex/etc) file",
                    default=None,
                    metavar="FILE")

            self.parser.add_option("--ignore-answer",
                    dest="ignore_answer",
                    action="store_true",
                    help="do not wait for answer to BSL commands",
                    default=False)

            self.parser.add_option("--control-delay",
                    dest="control_delay",
                    type="float",
                    help="Set delay in seconds (float) for BSL start pattern",
                    default=0.05)

            self.parser.add_option_group(group)


        def close_connection(self):
            self.close()

        def open_connection(self):
            self.open(
                self.options.port,
                ignore_answer = self.options.ignore_answer,
            )
            self.control_delay = self.options.control_delay

            if self.options.invert_test:
                self.invertTEST = True
                self.set_TEST(True)

            if self.options.invert_reset:
                self.invertRST= True
                self.set_RST(True)

            if self.options.start_pattern:
                self.start_bsl()

            logger = logging.getLogger('BSL')

            if self.options.do_mass_erase:
                self.extra_timeout = 6
                self.mass_erase()
                self.extra_timeout = None
                self.BSL_TXPWORD("\xff"*32)
                # erase mass_erase from action list so that it is not done twice
                self.remove_action(self.mass_erase)
            else:
                if self.options.password is not None:
                    password = msp430.memory.load(self.options.password).get_range(0xffe0, 0xffff)
                    logger.info("Transmitting password: %s" % password.encode('hex'))
                    self.BSL_TXPWORD(password)

            if self.options.speed is not None:
                self.set_baudrate(self.options.speed)

                if self.options.verbose: logging.info("Done")




    bsl_target = SerialBSLTarget()
    bsl_target.main()
