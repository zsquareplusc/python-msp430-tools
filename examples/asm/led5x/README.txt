LED
===

Minimalistic assembler program that can be used to test the assembler and
download tools.

This version uses the peripherals on a 5xx/6xx device (WDT, PORT1), MSP430X
instructions and the upper Flash memory (starting at 0x10000).


Function
--------
This one toggles the pin P1.1.


Building
--------
Assembling and linking::

    python -m msp430.asm.as -x -o led.o4 led.S
    python -m msp430.asm.ld --mcu MSP430F5529 -o led.txt led.o4


Usage
-----
This is like the LED flashing example that comes preprogrammed on some of the
eval boards from TI. The eval boards from TI typically have a LED connected to
the pin P1.1.

Download::

    python -m msp430.bsl5.hid -e led.txt

The download could also be made with msp430.jtag.target or msp430.gdb.target

