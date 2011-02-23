LED
===

Example program for MSP430G2 Launchpad kit.


Function
--------
This one toggles the pin P1.0.


Building
--------
Assembling and linking::

    python -m msp430.asm.as -o led.o4 led.S
    python -m msp430.asm.ld --mcu MSP430G2231 --symbols MSP430G2231 -o led.titxt led.o4


Usage
-----
This is like the LED flashing example that comes preprogrammed on some of the
eval boards from TI. The eval boards from TI typically have a LED connected to
the pin P1.0.

Download::

    mspdebug rf2500 "prog led.titxt" exit

or with a recent MSP430.dll::

    python -m msp430.jtag.target -p TIUSB --spy-bi-wire -e led.titext
