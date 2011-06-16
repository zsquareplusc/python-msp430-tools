MSP430 Header Files
===================

The files are not included.

However, they can be downloaded manually. The ``fetchfiles.py`` script is there
to assist. It will download a snapshot of the header files from the
mspgcc.sf.net project and extract the files from there.

.. note::

    The script currently has a hard coded URL so not the latest file might be
    downloaded.


Installation
------------
Just open a shell in the include directory and execute the script::

        cd python-msp430-tools/msp430/asm/include
        python fetchfiles.py
