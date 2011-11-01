============
 Internals
============

Target APIs
===========
This is the API description for the target tools (up- and download of data to
MCU using different interfaces). See also the individual tools above and
:ref:`command_line_tools`.

The :class:`Target` class defines an interface that is implemented by all the
Target connections described here. This interface could be used for example in
custom programming tools or testing equipment in manufacturing.


Target base class
-----------------
.. module:: msp430.target


.. function:: identify_device(device_id, bsl_version)

    :param device_id: 16 bit number identifying the device
    :param bsl_version: 16 bit number identifying the ROM-BSL version
    :type device_id: int
    :type bsl_version: int
    :return: :data:`F1x`, :data:`F2x` or :data:`F4x`

    Identification of F1x, F2x, F4x devices.

.. class:: Target(object)

    This class implements a high level interface to targets. It also provides
    common code for command line tools so that e.g. the JTAG and BSL tools have
    a similar set of options.


    .. method:: memory_read(address, length)

        Read from memory

    .. method:: memory_write(address, data)

        Write to memory.

    .. method:: mass_erase()

        Clear all Flash memory.

    .. method:: main_erase()

        Clear main Flash memory (excl. infomem).

    .. method:: erase(address)

        Erase Flash segment containing the given address.

    .. method:: execute(address)

        Start executing code on the target.

    .. method:: version()

        The 16 bytes of the ROM that contain chip and BSL info are returned.

    .. method:: reset()

        Reset the device.


    Additional methods that can be override in subclass.

    .. method:: open_connection()

        Open the connection.

    .. method:: def close_connection()

        Close the connection.


    High level functions.

    .. method:: flash_segment_size(address)

        :param address: Address within MCU Flash memory
        :return: segment size in bytes

        Determine the Flasg segment size for a given address.

    .. method:: get_mcu_family()

        :return: :data:`F1x`, :data:`F2x` or :data:`F4x`

        Get MCU family. It calls :meth:`Version` to read from the device.

    .. method:: erase_infomem()

        Erase all infomem segments of the device.

    .. method:: upload(start, end)

        :param start: Start address of memory range (inclusive)
        :param end: End address of memory range (inclusive)

        Upload given memory range and store it in :attr:`upload_data`.

    .. method:: def upload_by_file()

        Upload memory areas and store it in :attr:`upload_data`. The
        ranges uploaded are determined by :attr:`download_data`.

    .. method:: program_file(download_data=None)

        :param download_data: If not None, download this. Otherwise :attr:`download_data` is used.

        Download data from :attr:`download_data` or the optional parameter.

    .. method:: verify_by_file()

        Upload and compare to :attr:`download_data`.

        Raises an exception when data differs.

    .. method:: erase_check_by_file()

        Upload address ranges used in :attr:`download_data` and check if memory is erased (0xff).
        Raises an exception if not all memory is cleared.

    .. method:: erase_by_file()

        Erase Flash segments that will be used by the data in self.download_data.


    Command line interface helper functions.

    .. method:: create_option_parser()

        :return: an :class:`optparse.OptionParser` instance.

        Create an option parser, populated with a basic set of options for
        reading and writing files, upload, download and erase options.

    .. method:: parse_args()

        Parse sys.argv now.

    .. method:: main()

        Entry point for command line tools.

    .. method:: add_extra_options()

        The user class can add items to :attr:`parser`.

    .. method:: parse_extra_options()

        The user class can process :attr:`options` he added.


    Actions list. This list is build and then processed in the command line tools.

    .. method:: add_action(function, \*args, \*\*kwargs)

        Store a function to be called and parameters in the list of actions.

    .. method:: remove_action(function)

        Remove a function from the list of actions.

    .. method:: do_the_work()

        Process the list of actions


.. exception:: UnsupportedMCUFamily

    Exception that may be raised by :class:`Target` when the connected MCU is
    not compatible.

.. data:: F1x
.. data:: F2x
.. data:: F4x


BSL Target
----------

Interface to the BSL in F1x, F2x, F4x.

.. module:: msp430.bsl.bsl

.. class:: BSL(object)

    Implement low-level BSL commands as well as high level commands.

    .. attribute:: MAXSIZE

        Maximum size of a block that can be read or written using low level
        commands.

    .. method:: checksum(data)

        :param data: A byte string with data
        :return: 16 checksum (int)

        Calculate the 16 XOR checksum used by the BSL over given data.


    Low level functions.

    .. method:: BSL_TXBLK(address, data)

        :param address: Start address of block
        :param data: Contents (byte string)

        Write given data to target. Size of data must be smaller than
        :attr:`MAXSIZE`

    .. method:: BSL_RXBLK(address, length)

        :param address: Start address of block
        :param length: Size of block to read
        :return: uploaded data (byte string)

        Read data from target. Size of data must be smaller than
        :attr:`MAXSIZE`

    .. method:: BSL_MERAS()

        Execute the mass erase command.

    .. method:: BSL_ERASE(address, option=0xa502)

        :param address: Address within the segment to erase.
        :param option: FCTL1 settings.

        Execute a segment or main-erase command.

    .. method:: BSL_CHANGEBAUD(bcsctl, multiply)

        :param bcsctl: BCSCTL1 settings for desired baud rate
        :param multiply: Baud rate multiplier (compared to 9600)

        Change the baud rate.

    .. method:: BSL_SETMEMOFFSET(address_hi_bits)

        :param address_hi_bits: Bits 16..19.

        For devices with >64kB address space, set the high bits of all
        addresses for BSL_TXBLK, BSL_RXBLK and BSL_LOADPC.

    .. method:: BSL_LOADPC(address)

        :param address: The address to jump to.

        Start executing code at given address. There is no feedback if the jump
        was successful.

    .. method:: BSL_TXPWORD(password)

        Transmit password to get access to protected functions.

    .. method:: BSL_TXVERSION()

        Read device and BSL info (byte string of length 16). Older
        ROM-BSL do not support this command.


    High level functions.

    .. method:: check_extended()

        Check if device has address space >64kB (BSL_SETMEMOFFSET needs to be
        used).

    See also :class:`msp430.target.Target` for high level functions

    .. method:: version()

        Read version. It tries :meth:`BSL_TXVERSION` and if that fails
        :meth:`BSL_RXBLK` from address 0x0ff0. The later only word if
        the device has been unlocked (password transmitted).

    .. method:: reset()

        Try to reset the device. This is done by a write to the WDT module,
        setting it for a reset within a few milliseconds.


.. exception:: BSLException(Exception)

    Errors from the slave.

.. exception:: BSLTimeout(BSLException)

    Got no answer from slave within time.

.. exception:: BSLError(BSLException)

    Command execution failed.


``msp430.bsl.target``
~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.bsl.target

This module can be executed as command line tool (``python
-m msp430.bsl.target``). It implements the BSL target tool.

.. class:: SerialBSL(bsl.BSL)

    Implement the serial port access.

    .. method:: open(port=0, baudrate=9600, ignore_answer=False)

        :param port: Port name or number
        :param ignore_answer: If set to true enables a mode where answers are not read.

        Open given serial port (pySerial).

        When ``ignore_answer`` is enabled, no answer will be read for any
        command. Instead a small delay will be made. This can be used for
        targets where only the TX line is connected.  However no upload and or
        verification of downloaded data is possible.

    .. method:: close()

        Close serial port

    .. method:: bsl(cmd, message='', expect=None)

        :param cmd: Command number to send
        :param message: Byte string with data to send.
        :param expect: The number of bytes expected in a data reply or None to disable check.
        :return: None on success with simple answers or a byte string for data answers.
        :raises bsl.BSLError: In case of unknown commands, broken packets
        :raises bsl.BSLTimeout: If no answer was received within time

        Implement the low level transmit-receive operation for BSL commands
        over the serial port. The ``cmd`` is filled in the data header,
        ``message`` appended and the checksum calculated for the sent packet.

        Received answers are checked. If ``expect`` is set a data reply must be
        received and its length must match the given number, otherwise a
        :exc:`bsl.BSLError` is raised.

    .. method:: set_RST(level=True)

        :param level: Signal level

        Set the RST pin to given level

    .. method:: set_TEST(level=True)

        :param level: Signal level

        Set the TEST or TCK pin to given level

    .. method:: set_baudrate(baudrate)

        :param baudrate: New speed (e.g. 38400)

        Send the change baud rate command and if successful change the baud
        rate of the serial port to the same value.

    .. method::: start_bsl()

        Generate the pulse pattern on RST and TEST/TCK that starts the ROM-BSL.


.. class:: SerialBSLTarget(SerialBSL, msp430.target.Target)

    Combine the serial BSL backend and the common target code.

    .. method:: add_extra_options()

        Adds extra options to configure the serial port and the usage of the
        control lines for RST and TEST/TCK.

    .. method:: parse_extra_options()

        Used to output additional tool version info.

    .. method:: close_connection()

        Close serial port.

    .. method:: open_connection()

        Open serial port, using the options from the command line (in
        :attr:`options`). This will also execute the mass erase command
        and/or transmit the password so that executing other actions
        is possible.

        This is also the place to download replacement BSL or the patch.

    .. method:: BSL_TXBLK

        Override the block write function to activate the patch if needed.

    .. method:: BSL_RXBLK

        Override the block read function to activate the patch if needed.

    .. method:: reset()

        Override the reset methods to use the RST control line signal (instead
        of the WDT access)


BSL5 Target
-----------
Interface to the BSL in F5x and F6x devices. UART and USB-HID are supported.

.. module:: msp430.bsl5.bsl5

.. class:: BSL5

    .. method:: check_answer(data)

        :param data: the data received from the target
        :return: None
        :raises: BSL5Error with the corresponding message if ``data`` contained an error code.


    Note that the length for the following memory read/write functions is
    limited by the packet size of the interface (USB-HID, UART).

    .. method:: BSL_RX_DATA_BLOCK(address, data)

        :param address: Location in target memory
        :param data: Byte string with data to write

        Write given data to target memory.

    .. method:: BSL_RX_DATA_BLOCK_FAST(address, data)

        :param address: Location in target memory
        :param data: Byte string with data to write

        Write given data to target memory. The target will not perform any
        checks and no respons is sent back.

    .. method:: BSL_TX_DATA_BLOCK(address, length)

        :param address: Location in target memory.
        :param length: Number of bytes to read.
        :return: Byte string with memory contents.

        Read from target memory.

    def BSL_MASS_ERASE()

        Execute the mass erase command.

    def BSL_ERASE_SEGMENT(address)

        :param address: An address within the segment to erase.

        Erase a single Flash memory segment.

    .. method:: BSL_LOAD_PC(address)

        :param address: Location in target memory.

        Start executing at given address. There is no check if the command is
        successful as the execution starts immediately.

    .. method:: BSL_RX_PASSWORD(password)

        :param password: Byte string with password (32 bytes)

        Transmit the password in order to unlock protected function of the BSL.

    .. method:: BSL_VERSION()

        :return: A tuple with 5 numbers.

        The return value contains the following numbers:

        - BSL vendor information
        - Command interpreter version
        - API version
        - Peripheral interface version

    .. method:: BSL_BUFFER_SIZE()

        :return: The maximal supported buffer size from the BSL.

    .. method:: BSL_LOCK_INFO()

        Toggle lock flag of infomem segment A (the one with calibration data).


    .. method:: BSL_CRC_CHECK(XXX)


    High level functions.

    .. method:: detect_buffer_size()

        Auto detect buffer size. Saved the result in :attr:`buffer_size`.
        Silently ignores if the command is not successful and keeps the old
        value.

    .. method:: memory_read(address, length)

        :param address: Location in target memory.
        :param length: The number of bytes to read.
        :return: A byte string with the memory contents.
        :raises BSL5Error: when :attr:`buffer_size` is undefined

        Read from memory. It creates multiple BSL_TX_DATA_BLOCK commands
        internally when the size is larger than the block size.

    .. method memory_write(address, data)

        :param address: Location in target memory.
        :param data: A byte string with the memory contents.
        :raises BSL5Error: when :attr:`buffer_size` is undefined

        Write to memory. It creates multiple BSL_RX_DATA_BLOCK (or
        BSL_RX_DATA_BLOCK_FAST) commands internally, when the size is larger
        than the block size. :attr:`use_fast_mode` selects if standard or fast
        mode command is used.

    .. method:: mass_erase()

        Clear all Flash memory.

    .. method:: erase(address)

        :param address: Address within the segment to erase.

        Erase Flash segment containing the given address

    #~ def main_erase(self):
        #~ Erase Flash segment containing the given address.

    .. method:: execute(address)

        :param address: Location in target memory.

        Start executing code on the target.

    .. method:: password(password)

        :param password: Byte string with password (32 bytes)

        Transmit the BSL password.

    .. method:: version()

        Get the BSL version. The 16 bytes of the ROM that contain chip and
        BSL info are returned.

    .. method:: reset()

        Reset target using the WDT module.


.. exception:: BSL5Exception(Exception)

    Common base class for errors from the slave

.. exception:: BSL5Timeout(BSL5Exception)

    Got no answer from slave within time.

.. exception:: BSL5Error(BSL5Exception)



``msp430.bsl5.hid``
~~~~~~~~~~~~~~~~~~~
.. module:: msp430.bsl5.hid

This module can be executed as command line tool (``python -m
msp430.bsl5.hid``). It implements the BSL protocol over USB-HID supported by
F5xx devices with buil-in USB hardware.

Currently implementations for Windows (pywinusb) and GNU/Linux are provided
(hidraw).

.. class:: HIDBSL5Base

   .. method:: bsl(cmd, message='', expect=None, receive_response=True)

        :param cmd: BSL command number.
        :param message: Byte string with data for command.
        :param expect: Enable optional check of response length.
        :param receive_response: When set to false, do not receive response.

        Low level access to the HID communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer. The first byte will be the response code from the BSL

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, the answer is just returned.

        Frame format::

            +------+-----+-----------+
            | 0x3f | len | D1 ... DN |
            +------+-----+-----------+

.. class:: HIDBSL5

    .. method:: open(device=None)

        :param device: Name of device to use or ``None`` for auto detection.

        Connect to target device.

        Auto detection searches for a device with USB VID:PID: 2047:0200.
        It may pick a random one if multiple devices with that ID are connected.

        Examples for the ``device`` parameter under GNU/Linux: ``/dev/hidraw4``.
        Windows currently does not support passing an explicit device (only
        auto detection).

    .. method:: close()

        Close connection to target.

    .. method:: write_report(data)

        :param data: Byte string with report for target. 1st byte is the report number.

        Write given data to the target device. The first bye of the data has to
        be the HID report number.

    .. method:: read_report()

        :return: Byte string with report from target. 1st byte is the report number.

        Read a HID report from the target. May block if no data is sent by the
        device.

.. class:: HIDBSL5Target(HIDBSL5, msp430.target.Target)

    Combine the HID BSL5 backend and the common target code.

    .. method:: add_extra_options()

        Populate the option parser with options for the USB HID connection and password.

    .. method:: close_connection()

        Close connection to target.

    .. method:: open_connection()

        connect to USB HID device using the options from the command line (in
        :attr:`options`). This will also execute the mass erase command
        and/or transmit the password so that executing other actions
        is possible.

        As USB devices only have a stub BSL, this also downloads a full
        BSL to the device RAM. The BSL is kept in the package as
        ``RAM_BSL.00.05.04.34.txt`` (loaded using :mod:`pkgdata`).

    .. method:: reset()

        Try to reset the device. This is done by a write to the WDT module,
        setting it for a reset within a few milliseconds.


``msp430.bsl5.uart``
~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.bsl5.uart

This module can be executed as command line tool (``python -m
msp430.bsl5.uart``). It implements the BSL target tool for F5xx/F6xx devices
w/o USB hardware (it uses the UART).

.. function:: crc_update(crc, byte)

    Calculate the 16 bit CRC that is used by the BSL. Input is byte-wise.
    The function can be used with ``reduce``::

        crc = reduce(crc_update, b"data", 0)

.. class:: SerialBSL5(bsl5.BSL5)

    .. attribute:: extra_timeout

        Extend timeout for responses by given number of seconds (int).

    .. attribute:: invertRST

        Invert signal on RST line (bool).

    .. attribute:: invertTEST

        Invert signal on TEST/TCK line (bool).

    .. attribute:: swapResetTest

        Exchange the control lines on the serial port (RTS/DTR) which are used
        for RST and TEST/TCK.

    .. attribute:: testOnTX

        Send BREAK condition on TX line (bool), additionally to use of TEST/TCK
        control line.

    .. attribute:: blindWrite

        Do not receive and responses (bool).

    .. attribute:: control_delay

        Delay in seconds (float) that is waited after each change of RTS or
        TEST/TCK line change.

    .. method:: open(port=0, baudrate=9600, ignore_answer=False)

        Initialize connection to a serial BSL.

    .. method:: close()

        Close serial port.

    .. method:: BSL_CHANGE_BAUD_RATE(multiply)

        :param multiply: Multiplier of baud rate compared to 9600.

        Low level command to change the BSL baud rate on the target.

    .. method:: bsl(cmd, message='', expect=None)

        :param cmd: BSL command number.
        :param message: Byte string with data for command.
        :param expect: Enable optional check of response length.
        :param receive_response: When set to false, do not receive response.

        Low level access to the serial communication.

        This function sends a command and waits until it receives an answer
        (including timeouts). It will return a string with the data part of
        the answer. In case of a failure read timeout or rejected commands by
        the slave, it will raise an exception.

        If the parameter "expect" is not None, "expect" bytes are expected in
        the answer, an exception is raised if the answer length does not match.
        If "expect" is None, the answer is just returned.

        Frame format::

            +-----+----+----+-----------+----+----+
            | HDR | LL | LH | D1 ... DN | CL | CH |
            +-----+----+----+-----------+----+----+

    .. method:: set_RST(level=True)

        :param level: Signal level.

        Controls RST/NMI pin (0: GND; 1: VCC; unless inverted flag is set)

    .. method:: set_TEST(level=True)

        :param level: Signal level.

        Controls TEST pin (inverted on board: 0: VCC; 1: GND; unless inverted
        flag is set)

    .. method:: set_baudrate(baudrate)

        Change the BSL baud rate on the target and switch the serial port.

    .. method:: start_bsl()

        Start the ROM-BSL using the pulse pattern on TEST and RST.


.. class:: SerialBSL5Target(SerialBSL5, msp430.target.Target)

    Combine the serial BSL backend and the common target code.

    .. method:: add_extra_options()

        Populate the option parser with options for the serial port and password.

    .. method:: parse_extra_options()

        Prints additional version info.

    .. method:: close_connection()

        Close connection to target.

    .. method:: open_connection()

        Open serial port, using the options from the command line (in
        :attr:`options`). This will also execute the mass erase command
        and/or transmit the password so that executing other actions
        is possible.

    .. method:: reset()

        Try to reset the device. This is done by a write to the WDT module,
        setting it for a reset within a few milliseconds.


JTAG Target
-----------
interface to JTAG adapters (USB and parallel port).

``msp430.jtag.clock``
~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.jtag.clock

.. note:: This module is currently only supported with parallel port JTAG adapters and MSP430mspgcc.dll/so


.. function:: getDCOFreq(dcoctl, bcsctl1, bcsctl2=0)

    :return: frequency in Hz

    Measure DCO frequency on a F1xx or F2xx device.

.. function:: setDCO(fmin, fmax, maxrsel=7, dcor=False)

    :return: (frequency, DCOCTL, BCSCTL1)

    Software FLL for F1xx and F2xx devices.

.. function:: getDCOPlusFreq(scfi0, scfi1, scfqctl, fll_ctl0, fll_ctl1)

    :return: frequency in Hz.

    Measure DCO frequency on a F4xx device

.. function:: setDCOPlus(fmin, fmax)

    :return: (frequency, SCFI0, SCFI1, SCFQCTL, FLL_CTL0, FLL_CTL1)

    Software FLL for F4xx devices.


``msp430.jtag.dco``
~~~~~~~~~~~~~~~~~~~
.. module:: msp430.jtag.dco

.. note:: This module is currently only supported with parallel port JTAG adapters and MSP430mspgcc.dll/so

MSP430 clock calibration utility.

This tool can measure the internal oscillator of F1xx, F2xx and F4xx devices
that are connected to the JTAG. It can  display the supported frequencies, or
run a software FLL to find the settings for a specified frequency.

This module can be executed as command line tool (``python -m
msp430.jtag.dco``).

.. function:: adjust_clock(out, frequency, tolerance=0.02, dcor=False, define=False)

    Detect MSP430 type and try to set the clock to the given frequency.
    When successful, print the clock control register settings.

    This function assumes that the JTAG connection to the device has already
    been initialized and that the device is under JTAG control and stopped.

.. function:: measure_clock()

    :return: A dictionary with information about clock speeds (key depend on MCU type).

    Measure fmin and fmax of RSEL ranges or hardware FLL.

.. function:: calibrate_clock(out, tolerance=0.002, dcor=False)

    Recalculate the clock calibration values and write them to the Flash.

    .. note:: currently for F2xx only

``msp430.jtag.jtag``
~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.jtag.jtag

JTAG programmer for the MSP430 embedded processor.

Requires Python 2+ and the binary extension _parjtag or ctypes
and MSP430mspgcc.dll/libMSP430mspgcc.so or MSP430.dll/libMSP430.so
and HIL.dll/libHIL.so

Constants used to identify backend implementations:

.. data:: PARJTAG
.. data:: CTYPES_MSPGCC
.. data:: CTYPES_TI


.. function:: locate_library(libname, paths=sys.path, loader=None)

    Search for a .DLL or .so library on the given list of paths.

.. function:: init_backend(force=None)

    :param force: One of PARJTAG, CTYPES_MSPGCC, CTYPES_TI or ``None``.

    Initializes the global :data:`backend` with a class that gives access to
    the JTAG library.

    The backend implementation is selected automatically when ``force`` is
    ``None``.


.. class:: JTAG

    High level access to the target for upload, download and funclets. Uses the
    :data:`backend` to communicate.


.. exception:: JTAGException(Exception)


``msp430.jtag.target``
~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.jtag.target

This module can be executed as command line tool (``python -m
msp430.jtag.target``).

.. class:: JTAGTarget(object)

    .. method:: def memory_read(address, length)

        Read from memory.

    .. method:: memory_write(address, data)

        Write to memory.

    .. method:: def mass_erase()

        Clear all Flash memory.

    .. method:: main_erase()

        Clear main Flash memory (excl. infomem).

    .. method:: erase(address)

        Erase Flash segment containing the given address.

    .. method:: execute(address)

        Start executing code on the target.

    .. method:: version()

        The 16 bytes of the ROM that contain chip and BSL info are returned.

    .. method:: reset()

        Reset the device.

    .. method:: close()

        Close connection to target.


.. class:: JTAG(JTAGTarget, msp430.target.Target)

    Combine the JTAG backend and the common target code.

    .. method:: help_on_backends()

        Implement option ``--target-help``.

    .. method:: add_extra_options()

        Populate option parser with options for JTAG connection.

    .. method:: parse_extra_options()

        Apply extra options (such as forcing a backend implementation)


    .. method:: close_connection()

        Close connection to target.

    .. method:: open_connection()

        Connect to target.

.. function:: main()

    Implements the command line frontend.


.. XXX implementation of backend


``msp430.jtag.profile``
~~~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.jtag.profile

Statistical profiler for the MSP430.

It works by sampling the address bus and counting addresses seen.  The problem
there is, that it is not sure that we're reading a valid address every time. An
other issue is the relatively slow sampling rate compared to the execution
speed of the MCU, which means that several runs are need to get meaningful
numbers.

This module can be executed as command line tool (``python -m
msp430.jtag.profile``).

.. note:: This module is currently only supported with parallel port JTAG adapters and MSP430mspgcc.dll/so

.. function:: main()

    Command line frontend. It connects to a target using JTAG. It then samples the
    address bus as fast as possible (which is still much slower that the
    typical CPU speed). When the tool is aborted with ``CTRL+C``, it outputs a
    list of addresses and the number of samples that were hit.

    The idea is that the data can be used to create a statistical analysis of
    code coverage and usage.

    There are a number of problems, so this tool has to be considered as
    experimental:

    - Sampling is relatively slow.
    - There is no guarantee that the value read from the address bus is
      correct. Samples may occur when the CPU is altering the value.
    - There is no difference between instruction fetch and data access.


GDB Target
----------
Interface to GDB servers (`msp430-gdbproxy`_, mspdebug_). This can be used to up-
and download data via the GDB servers. No debugging support is provided.

.. _mspdebug: http://mspdebug.sf.net
.. _`msp430-gdbproxy`: http://mspgcc.sf.net


``msp430.gdb.gdb``
~~~~~~~~~~~~~~~~~~
.. module:: msp430.gdb.gdb

.. exception:: GDBException(Exception)

    Generic protocol errors.

.. exception:: GDBRemoteTimeout(GDBException)

    If target does not answer.

.. exception:: GDBRemoteTooManyFailures(GDBException)

    If target does not answer.

.. exception:: GDBUnknownCommandError(GDBException)

    If target does not know this command.

.. exception:: GDBRemoteError(GDBException)

     .. method :: getErrorCode()

        :return: The error code that was received from the GDB server.

.. class:: ClientSocketConnector(threading.Thread)

    Make a connection through a TCP/IP socket. This version connects to a
    server (i.e. is a client).

    .. method:: __init__(host_port)

        The host/port tuple from the parameter is used to open a TCP/IP
        connection. It is passed to ``socket.connect()``.

    .. method:: write(text)

        Just send everything

    .. method close()

        Close connection.

    .. method run()

        Implement an efficient read loop for sockets.

.. class:: GDBClient(ClientSocketConnector)

    .. method:: __init__(\*args, \*\*kwargs)

        All parameters are passed to :meth:`ClientSocketConnector.__init__`

    .. method:: handle_partial_data(data)

        :param data: Byte string with received data from the GDB server.

        Process received data. It may be partial, i.e. no complete line etc.

    .. method:: handle_packet(packet)

        :param packet: A packet received from the GDB server.

        Called by :meth:`handle_partial_data` when a complete packet from the
        GDB server was decoded.


    Callbacks (can be overridden in subclasses):

    .. method:: output(message)

        Called on ``o`` (output) packages. These are used by the GDB server to
        write messages for the user.


    Commands:

    .. method:: set_extended()

        Set extended mode. Expected answer empty string or or ``OK``

    .. method:: last_signal()

        :return: Stop Reply Packets

        Get last signal.

    .. method:: cont(startaddress=None, nowait=False)

        :return: Stop Reply Packets

        Continue execution on target.

    .. method:: cont_with_signal(signal, startaddress=None)

        :param signal: Signal number that is sent to the target.
        :return: Stop Reply Packets

        Continue with signal.

    .. method:: read_registers()

        :return: List of values of the regsiters (1 ... 16)

        Read all registers.

    .. method:: write_registers(registers)

        :param registers: List with values for all registers (list of 16 ints).

        Write all registers.

    .. method:: cycle_step(cycles, startaddress=None)

        :param cycles: Run the given number of cycles on the target.

        Cycle step (draft).

    .. method:: read_memory(startaddress, size)

        :param startaddress: Address on target.
        :param size: Number of bytes to read.
        :return: Byte string with memory contents

        Read memory.

    .. method:: write_memory(startaddress, data)

        :param startaddress: Address on target.
        :param data: Byte string with memory contents

        Read memory.

    .. method:: read_register(regnum)

        :param regnum: Register number.
        :return: integer (register contents)

        Read single register.

    .. method:: write_register(regnum, value)

        :param regnum: Register number.
        :param value: integer (register contents)

        Write single register.
        expected answer 'OK' or 'Enn'"""

    .. method:: query(query, nowait=False)

        :param query: String with query for the GDB server.

        Send general query to GDB server.

    .. method:: set(name, value)

        :param name: Name of the setting.
        :param value: New value for the setting.

        Configure a setting.

    .. method:: step(startaddress = None):

        :return: Stop Reply Packets

        Single step on target.

    .. method:: step_with_signal(signal, startaddress=None)

        :param signal: Signal number that is sent to the target.
        :return: Stop Reply Packets

        Step with signal.

    .. method:: write_memory_binary(startaddress, data)

        Write data to target, with binary transmission to GDB server. May not
        be supported by all servers.

    .. method:: remove_breakpoint(type, address, length)

        Remove break or watchpoint (draft)

    .. method:: set_breakpoint(type, address, length)

        Insert break or watchpoint (draft).

    .. method:: monitor(command, nowait=False)

        Pass commands to a target specific interpreter in the GDB server.
        Servers for the MSP430 often implement commands such as ``erase``.

    .. method:: interrupt()

        Send Control+C. May be used to stop the target if it is running (e.g.
        after a continue command). No effect on a stopped target.
 

``msp430.gdb.target``
~~~~~~~~~~~~~~~~~~~~~
.. module:: msp430.gdb.target

Remote GDB programmer for the MSP430 embedded processor.

This module can be executed as command line tool (``python -m
msp430.gdb.target``).

.. class:: GDBTarget(object)

    .. method:: memory_read(address, length)

        Read from memory.

    .. method:: memory_write(address, data)

        Write to memory.

    .. method:: mass_erase()

        Clear all Flash memory.

    .. method:: main_erase()

        Clear main Flash memory (excl. infomem).

    .. method:: erase(address)

        Erase Flash segment containing the given address.

    .. method:: execute(address)

        Start executing code on the target.

    .. method:: version()

        The 16 bytes of the ROM that contain chip and BSL info are returned.

    .. method:: reset()

        Reset the device.

    .. method:: open(host_port)

        :param host_port: A tuple ``(str, port)`` with target host address and port number.

    .. method:: close()


.. class:: GDB(GDBTarget, msp430.target.Target)

    Combine the GDB backend and the common target code.

    .. method:: add_extra_options()

        Populate option parser with GDB client specific options.

    .. method:: close_connection()

        Close connection to target.

    .. method:: open_connection()

        Connect to target applying the command line options.


Utility APIs
============

``msp430.memory``
-----------------
.. module:: msp430.memory

.. class:: DataStream(object)

    An iterator for addressed bytes. It yields all the bytes of a
    :class:`Memory` instance in ascending order. It allows peeking at the
    current position by reading the :attr:`address` attribute. ``None`` signals
    that there are no more bytes (and :meth:`next()` would raise
    :exc:`StopIteration`).

    .. method:: __init__(self, memory)

        Initialize the iterator. The data from the given memory instance is
        streamed.

    .. method:: next()

        Gets next tuple (address, byte) from the iterator.

    .. attribute:: address

        The address of the byte that will be returned by :meth:`next()`.


.. function:: stream_merge(\*streams)

    :param streams: Any number of :class:`DataStream` instances.

    Merge multiple streams of addressed bytes. If data is overlapping, take
    it from the later stream in the list.


.. class:: Segment(object)

    Store a string or list with memory contents (bytes) along with its start
    address.

    .. method:: __init__(startaddress = 0, data=None)

        :param startaddress: Address of 1st byte in data.
        :param data: Byte string.

        Initialize a new segment that starts at given address, containing the
        given data.

    .. method:: __getitem__(index)

        :param index: Index of byte to get.
        :return: A byte string with one byte.
        :raises IndexError: offset > length of data

        Read a byte from the segment. The offset is 0 for the 1st byte in the
        block.

    .. method:: __len__()

        Return the number of bytes in the segment.

    .. method:: __cmp__(other)

        Compare two segments. Implemented to support sorting a list of segments
        by address.

.. class:: Memory(object)

    Represent memory contents.

    .. method:: __init__()

        Initialize an empty memory object.

    .. method:: append(segment)

        :param segment: A :class:`Segment` instance.

        Append a segment to the internal list. Note that there is no check for
        overlapping data.

    .. method:: __getitem__(index)

        :return: :class:`Segment` instance
        :raises IndexError: index > number of segments

        Get a segment from the internal list.

    .. method:: __len__()

        :return: Number of segments in the internal list.


    .. method:: get_range(fromadr, toadr, fill='\xff')

        :param fromadr: Start address (including).
        :param toadr: End address (including).
        :param fill: Fill value (a byte).
        :return: A byte string covering the given memory range.

        Get a range of bytes from the memory. Unavailable values are filled
        with ``fill`` (default 0xff).

    .. method:: get(address, size)

        :param address: Start address of block to read.
        :param size: Size of the of block to read.
        :return: A byte string covering the given memory range.
        :exception ValueError: unavailable addresses are tried to read.

        Get a range of bytes from the memory.

     .. method:: set(address, contents)

        :param address: Start address of block to read.
        :param contents: Bytes to write to the memory.
        :exception ValueError: Writing to an undefined memory location.

        Write a range of bytes to the memory. A segment covering the address
        range to be written has to be existent. A :exc:`ValueError` is raised
        if not all data could be written (attention: a part of the data may
        have been written!). The contents may span multiple (existing)
        segments.

    .. method:: merge(other)

        :param other: A Memory instance, its contents is copied to this instance.

        Merge an other memory object into this one. The data is merged: in case
        of overlapping, the data from ``other`` is used. The segments are
        recreated so that consecutive blocks of bytes are each in one segment.


.. function:: load(filename, fileobj=None, format=None)

    :param filename: Name of the file to open
    :param fileobj: None to let this function open the file or an open, seekable file object (typically opened in binary mode).
    :param format: File format name, ``None`` for auto detection.
    :return: Memory object.

    Return a Memory object with the contents of a file.
    File type is determined from extension and/or inspection of content.


.. function:: save(memory, fileobj, format='titext')

    :param fileobj: A writeable file like object (typically opened in binary mode).
    :param format: File format name.

    Save given memory object to file like object.


``msp430.listing``
------------------
.. module:: msp430.listing

This module provides parser for listing/map files of the IAR and mspgcc C
compilers. This can be used in tools that need to know the addresses of
variables or functions. E.g. to create a checksum patch application.

Sub-modules:

- ``msp430.listing.iar``
- ``msp430.listing.mspgcc``

Each module provides such a function:

.. function:: label_address_map(filename)

    :param filename: Name of a listing or map file.
    :return: A dictionary mapping labels (key) to addresses (values/int).


File format handlers
====================

Overview
--------
The file format handler modules each provides a load and/or save function on
module level.

.. function:: load(filelike)

    :param filelike: A file like object that is used to write the data.
    :return: :class:`msp430.memory.Memory` instance with the contents loaded from the fike like object.

    Read from a file like object and fill in the contents to a memory object.
    The file like should typically be a file opened for reading in binary
    mode.

.. function:: save(memory, filelike)

    :param memory: :class:`msp430.memory.Memory` instance with the contents loaded from the fike like object.
    :param filelike: A file like object that is used to write the data.

    Write the contents of the memory object to the given file like object. This
    should typically be a file opened for writing in binary mode.

Handlers
--------
``msp430.memory.bin``

    .. module:: msp430.memory.bin

    Load and save binary data. Note that this is not practical for MSP430 binaries
    as they usually are not one block and do not start at address null. The binary
    format can not keep track of addresses.

``msp430.memory.elf``

    ELF object file reader (typical file extension ``.elf``). There is
    currently no support for writing this type.

``msp430.memory.hexdump``

    Read and write hex dumps.

``msp430.memory.titext``

    Read and write TI-text format files (often named ``.txt``).

``msp430.memory.intelhex``

    Read and write Intel-HEX format files (often named ``.a43``).

