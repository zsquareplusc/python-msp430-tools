=================
 Shell utilities
=================

The module :mod:`msp430.shell` provides some useful scripts for the shell.

``msp430.shell.command``
========================

This tool emulates a number of shell utilities. The idea is that makefiles or
similar build tools can use these commands to be OS independent (so that the
same set of commands works on Windows, GNU/Linux, etc.).

Command collection:

- ``cat``     Show file contents.
- ``cp``      Copy files.
- ``expand``  Expand shell patterns ("\*.c", "?" etc.).
- ``false``   Simply return exit code 1
- ``list``    This text.
- ``mkdir``   Create directories.
- ``mv``      Move/rename files.
- ``rm``      Delete files/directories.
- ``touch``   Update file date, create file.
- ``true``    Simply return exit code 0

More help with "command.py COMMAND --help"

Example::

    python -m msp430.shell.command rm -f no_longer_needed.txt
    python -m msp430.shell.command cp src.txt dst.txt


``msp430.shell.watch``
======================

This tool watches one or multiple files for changes. When a change on one file
is detected it runs a given command. This could be used e.g. to automatically
trigger a download when a hex file has changed or trigger compilation when one
of the source files has changed.

Usage: watch.py FILENAME \[FILENAME...\] --execute "some/program/ --"

Options:
  -h, --help            show this help message and exit
  -x COMMAND, --execute=COMMAND
                        run this command when watched file(s) changed, -- is
                        replaced by FILENAME(s)

