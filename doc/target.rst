==============
 Target Tools
==============

This is the API description for the target tools (up- and download of data to
MCU using different interfaces). See also :ref:`command_line_tools`.


Target base class
=================
.. module:: msp430.target


.. function:: idetify_device(device_id, bsl_version)

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
==========

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
---------------------
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
===========
Interface to the BSL in F5x and F6x devices. UART and USB-HID are supported.

.. module:: msp430.bsl5.bsl5
.. class:: BSL5

``msp430.bsl5.hid``
-------------------
.. module:: msp430.bsl5.hid

This module can be executed as command line tool (``python -m
msp430.bsl5.hid``). It implements the BSL protocol over USB-HID supported by
F5xx devices with buil-in USB hardware.

Currently implementations for Windows (pywinusb) and GNU/Linux are provided
(hidraw).

.. class:: HIDBSL5Base
.. class:: HIDBSL5

``msp430.bsl5.uart``
--------------------
.. module:: msp430.bsl5.uart

This module can be executed as command line tool (``python -m
msp430.bsl5.uart``). It implements the BSL target tool for F5xx/F6xx devices
w/o USB hardware (it uses the UART).

.. class:: SerialBSL5(bsl5.BSL5)
.. class:: SerialBSL5Target(SerialBSL5, msp430.target.Target)


JTAG Target
===========
interface to JTAG adapters (USB and parallel port).


GDB Target
==========
Interface to GDB servers (msp430-gdbproxy, mspdebug). This can be used to up-
and download data via the GDB servers. No debugging support is provided.

