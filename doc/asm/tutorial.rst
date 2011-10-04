
Tutorial
========

A simple example
----------------
The assembler ``msp430.asm.as`` reads source files (``*.S``) and creates object
files (``*.o4``). Multiple object files are then linked together and a binary
is created that can be downloaded to the MCU.

For example, ``led.S``::

    ; Test program for msp430.asm.as and msp430.asm.ld
    ;
    ; This one toggles the pin P1.1. This is like the LED flashing example that
    ; comes preprogrammed on some of the eval boards from TI.

    .text
            ; entry point after device reset
    RESET:  mov     #0x5a80, &0x120         ; disable WDT
            bis.b   #1, &0x22               ; set pin to output

            ; loop toggling the pin and then doing a delay
    .L1:    xor.b   #1, &0x21               ; toggle pin
            mov     #0xc350, R15            ; init delay loop
    .L2:    dec     R15                     ; count down
            jnz     .L2                     ; jump while counter is not zero
            jmp     .L1                     ; loop the toggling part


    ; set the reset vector (and all the others) to the program start
    .section .vectors
            .word  RESET, RESET, RESET, RESET, RESET, RESET, RESET, RESET
            .word  RESET, RESET, RESET, RESET, RESET, RESET, RESET
            .word  RESET                    ; reset vector

Assemble, link::

    python -m msp430.asm.as led.S -o led.o4
    python -m msp430.asm.ld --mcu MSP430G2211 led.o4 -o led.titext

Download
--------

There are several ways to get a program into a MSP430.

Boot Strap Loader (BSL), Serial
    Using a serial connection and some ROM code in the MSP430 it is possible to
    read and write memory, including Flash.

    Not all devices support BSL (e.g. the smaller value line (G2) and F2 devices)

    Command example (F1x, F2x, F4x)::

        python -m msp430.bsl.target -e led.titext

    Command example (F5x, F6x)::

        python -m msp430.bsl5.uart -e led.titext

Boot Strap Loader (BSL), USB HID
    Some MSP430 have a built in USB controller and they also support downloading
    through USB.

    Command example::

        python -m msp430.bsl5.hid -e led.titext

JTAG, 4-wire
    This interface gives access to the internals of the CPU so that it not only
    can be used to up and download memory, it is also possible to set breakpoints,
    single step and more debugging.

    Some devices have shared GPIO pins, so that a TEST pin switches the
    function from normal IO pin to JTAG.

    Command example::

        python -m msp430.jtag.target -e led.titext

JTAG, spy-bi-wire
    This is a variation of the JTAG interface that only requires two pins and
    does not occupy GPIO pins. The same signals as in a 4-wire connection are
    serialized and transmitted over these two lines. This means that the maximum
    speed of the spy-bi-wire interface is slower than the 4-wire interface.

    Many new MSP430 support this interface (not F1, F4).

    Command example::

        python -m msp430.jtag.target --spy-bi-wire -e led.titext


The python-msp430-tools also support downloading via remote-GDB-protocol. If a
GDB server is running (same machine or a different one), ``msp430.gdb.target``
can be used. GDB servers are `msp430-gdbproxy`_ or mspdebug_


Notes for JTAG
~~~~~~~~~~~~~~
Windows
    The `MSP430.dll`_ can be downloaded from TI.
    With this installed, USB and parallel port adapters can be used with the
    ``msp430.jtag.target`` tool.

Linux / Others
    There is no (recent) MSP430.dll available.

    USB JTAG adapters can be used with the tool mspdebug_ (also includes debug support).

    Parallel port adapters can be used with MSP430mspgcc_ (no debug support).

    Command example (Launchpad or ez430-rf2500 kits)::

        mspdebug rf2500 "prog led.titext" exit

.. _mspdebug: http://mspdebug.sf.net
.. _MSP430mspgcc: http://mspgcc.cvs.sourceforge.net/viewvc/mspgcc/jtag/
.. _`msp430-gdbproxy`: http://sourceforge.net/projects/mspgcc/files/Outdated/msp430-gdbproxy/
.. _`MSP430.dll`: http://processors.wiki.ti.com/index.php/MSP430_JTAG_Interface_USB_Driver


Installing header files
-----------------------
The example above directly used the addresses of the peripheral modules - this
is not comfortable. It is easily possible to use the header files from TI as a C
preprocessor (``cpp``) is included, however the header files itself are not.


Downloading header files
~~~~~~~~~~~~~~~~~~~~~~~~
A download and extraction script is located in the directory
``msp430/asm/includes``. When executed (``python fetch.py``) it will download
the ``msp430mcu`` archive from http://mspgcc.sf.net. Once downloaded, the files
are extracted to a subdirectory called ``upstream``.

The include and include/upstream directories are part of the search path for
cpp. Files in these directories are found automatically.

.. note:: The file name that is downloaded is currently hard coded in the
          script. It may make sense to check the site online for newer files.

Using the msp430mcu package
~~~~~~~~~~~~~~~~~~~~~~~~~~~
On many GNU/Linux systems it is possible to install the package ``msp430mcu``
though the systems package management.

Debian/Ubuntu: `apt://msp430mcu`_

.. note:: The header files from the package are currently not found automatically.
          The user has to provide the location with the ``-I`` parameter of cpp.

.. _`apt://msp430mcu`: apt://msp430mcu


.. The preprocessor ``cpp`` can be used to read the MSP430 header files and use the
.. definitions of the peripherals. It also supports ``#define``, ``#if`` etc.


More Examples
-------------
A number of examples can be found in the ``examples/asm`` directory of the
``python-msp430-tools`` distribution.
