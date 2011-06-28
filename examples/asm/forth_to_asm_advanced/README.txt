========================
 Forth Demo Application
========================

Overview
========
This is an other example for the Forth to Assembler compiler that is included
with the python-msp430-tools.

Target hardware:

- TI Launchpad kit

- A CPU with Timer A (e.g. the MSP430G2231)


Features:

- use of clock calibration values (1MHz)

- Timer A is used as UART, settings: 2400,8,N,1

  - Lines (up to 8 characters) are read into a buffer

  - Line is parsed for commands, see protocol_ below

- WDT module is used as interval timer.

  - RED LED is flashing periodically

- an event handler (dispatching functions in the foreground, triggered by e.g.
  interrupts)

- showing the interrupt syntax


.. warning::

    This example should not be taken as "best practise"

The example implements a lot in Forth that I personally would not implement
that way for a "real" application. E.g. the serial reception suffers from the
additional overhead of interrupts programmed in Forth while an Assembler (or C)
snippet would only use a fraction of the space and time. The WDT interrupt
could be slowed down by using the ACLK/LFCLK so that no SLOWDOWN variable would
be needed.


Installation
============
A [GNU] make program must be available on the system. The software can be
translated with::

    $ make
    python -m msp430.shell.command rm -f demo.titext *.o4 demo.s-cpp demo.S \
                  startup.s-cpp \
                  intvec.s-cpp io.forth \
                  write.s-cpp putchar.S timer_a_uart_rx.S
    python -m msp430.asm.lib -o startup.s-cpp asm/startup.S
    python -m msp430.asm.as  -o startup.o4 startup.s-cpp
    python -m msp430.asm.h2forth  -o io.forth msp430g2231.h
    python -m msp430.asm.forth -DMCU=msp430g2231 -o demo.S demo.forth
    python -m msp430.asm.cpp  -o demo.s-cpp demo.S
    python -m msp430.asm.as  -o demo.o4 demo.s-cpp
    python -m msp430.asm.cpp  -o intvec.s-cpp intvec.S
    python -m msp430.asm.as  -o intvec.o4 intvec.s-cpp
    python -m msp430.asm.lib -o write.s-cpp asm/write.S
    python -m msp430.asm.as  -o write.o4 write.s-cpp
    python -m msp430.asm.lib -o putchar.S asm/timer_a_uart/putchar_outmod.S
    python -m msp430.asm.cpp  -o putchar.s-cpp putchar.S
    python -m msp430.asm.as  -o putchar.o4 putchar.s-cpp
    python -m msp430.asm.lib -o timer_a_uart_rx.S asm/timer_a_uart/receive_interrupt.S
    python -m msp430.asm.cpp  -o timer_a_uart_rx.s-cpp timer_a_uart_rx.S
    python -m msp430.asm.as  -o timer_a_uart_rx.o4 timer_a_uart_rx.s-cpp
    python -m msp430.asm.ld -v --mcu msp430g2231 -o demo.titext startup.o4 demo.o4 intvec.o4 write.o4 putchar.o4 timer_a_uart_rx.o4
    Segments used:
       RAM                            0x0200-0x0231       50 B  LE
          .bss                        0x0200-0x0231       50 B  LE
       FLASH                          0xf800-0xffcf     2000 B  LE, downloaded
          .text                       0xf800-0xffcf     2000 B  LE, downloaded
       .vectors                       0xffe0-0xffff       32 B  LE, downloaded
    rm demo.s-cpp intvec.s-cpp demo.S timer_a_uart_rx.s-cpp putchar.s-cpp


Downloading file ``demo.titext`` to the Launchpad under GNU/Linux using mspdebug_::

    $ make download-mspdebug

.. _mspdebug: http://mspdebug.sf.net

Testing
-------

The module ``xprotocol.py`` implements helper functions for the protocol_
described below. When it is started it runs a few tests::

    $ python xprotocol.py
    test_echo (__main__.TestCommands) ... ok
    test_error (__main__.TestCommands) ... ok
    test_load (__main__.TestCommands) ... 
    ~12 echo commands/second
    ok
    test_int (__main__.TestDecoder) ... ok
    test_str (__main__.TestDecoder) ... ok
    test_unknown (__main__.TestDecoder) ... ok

    ----------------------------------------------------------------------
    Ran 6 tests in 5.302s

    OK


Protocol
========
A simple line based protocol is talked on the serial port. The PC sends a
command (a line consisting of at least one character) to the Launchpad. It
interprets this command and may return multiple lines of output. The output
always ends with either ``xOK`` or ``xERR``. All other lines are also prefixed
with a character indicating the data that follows.

Example
-------
A terminal program is required. One possibility is (pySerial >= 2.6 is
required)::

    python -m serial.tools.miniterm /dev/ttyACM0 2400

Getting help. Transmitting ``h`` and ENTER::

    oCommands:
    o 's'       Read switch
    o 'oM..'    Echo message
    o 'c'       Dump calibration
    o 'mHHHH'   Hex dump of given address
    xOK

Reading out the calibration values with the command ``c``::

    h 10C0  54 B2 FE 26 FF FF FF FF FF FF FF FF FF FF FF FF  T��&������������
    h 10D0  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF  ����������������
    h 10E0  FF FF FF FF FF FF FF FF FF FF 10 10 FF FF FF FF  ����������..����
    h 10F0  FF FF FF FF FF FF FF FF FF FF FF FF 01 02 BC 86  ������������..��
    xOK

Or the CPU identification ``m0ff0`` (only 1st line is relevant)::

    h 0FF0  F2 01 30 40 00 00 00 00 00 00 00 00 01 02 00 00  �.0@............
    h 1000  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF  ����������������
    h 1010  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF  ����������������
    h 1020  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF  ����������������
    xOK

Reading the switch twice with ``s``::

    i0x0000
    xOK
    i0xffff
    xOK

Errors are of course reported too (input: ``fail``)::

    xERR (try 'h') unknown command:fail

