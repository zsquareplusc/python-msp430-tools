
Tutorial
========

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

Assemble, link, download::

    python -m msp430.asm.as led.S -o led.o4
    python -m msp430.asm.ld --mcu MSP430F1121 led.o4 -o led.titext

    python -m msp430.bsl.target -e led.titext

The preprocessor ``cpp`` can be used to read the MSP430 header files and use the
definitions of the peripherals. It also supports ``#define``, ``#if`` etc.


Installing header files
-----------------------
The example above directly used the addresses of the peripheral modules - this
is not comfortable. Its easily possible to use the header files from TI as a C
preprocessor is included, however the header files itself are not.


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


Examples
--------
A number of examples can be found in the ``examples/asm`` directory of the
``python-msp430-tools`` distribution.
