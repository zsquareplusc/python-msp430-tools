Forth Cross Compiler
====================

The package also includes a limited Forth_ like language cross compiler.

.. warning:: This feature is under development.

.. attention:: Documentation is incomplete. Also reading the source is recommended.

Traditional methods to use Forth on a different target system involve
meta-compilers and the assembler for the target is often implemented in Forth_
itself. Not this one.

The idea of this tool chain is to cross compile Forth_ into assembler for
the MSP430 and then use the normal assembler and linker. This means that other
assembler (or C modules etc.) can be combined in one program.

::

    led.forth -> led.S -> led.o4     --+--> led.titext
              intvec.S -> intvec.o4  --/
             startup.S -> startup.o4 --/

Available Words
---------------

A list of supported words is available here:

.. toctree::
    :maxdepth: 1

    forth_words

Availability of words depends on their definition. There are words that can
only be executed on the host. These words can not be used within definitions
that are cross compiled. In contrast, ``CODE`` words are only allowed within
definitions that are cross compiled. Normal definitions using ``:`` can run on
host and target, unless they depend on words described before. In that case the
restrictions of that type applies.



Command line tools
------------------
msp430.asm.forth
~~~~~~~~~~~~~~~~
This is itself a Forth_ interpreter and is used to do the conversion into an
assembler file for the MSP430.

msp430.asm.h2forth
~~~~~~~~~~~~~~~~~~
This tool can be used to convert C header to a Forth_ file. Each ``#define``
will be turned into a ``CONSTANT``. It's main purpose is to get access to the
peripheral an bit definitions from the TI header files.


Cross compilation
-----------------
The file given to ``msp430.asm.forth`` is executed on the host.

Only words used in the program for the target are translated. This makes the
use of libraries simple - it does not matter how many words are defined or used
by the program on the host.

There are three dictionaries in the host interpreter.

- built-in name space: The words here are implemented in Python (the language the
  host interpreter is written in). These can not be cross compiled (unless they
  are provided in the target dictionary).

- normal name space: normal ``:``/``;`` definitions go here. The words here can
  be used on the host as well as on the target.

- target name space: ``CODE`` definitions go here. These words can be referenced
  by the host but they can not be executed (they won't do the expected).

All three dictionaries are available to the host but cross compiled words must
exist in one of the later two.


Cross compilation of normal words (``:``)
    The words are already translated into a list of references by the host
    interpreter. They can be output 1:1 as list of words for the target
    (exceptions are branch distances, they are multiplied by two).

Cross compilation of ``CODE`` words
    These words are executed to get the cross compilation. So each ``CODE``
    word simply outputs assembler code. Forth_ words must include the code
    for ``NEXT``.

    This allows that ``CODE`` word definitions can also be used to generate
    helper functions for other assembler parts.

Cross compilation of ``INTERRUPT`` words
    A special assembler start code is included and the exit functionality
    is handled specially. The function itself is translated the same way
    a normal word is.


MSP430 specific features
------------------------

- ``VARIABLE`` and ``VALUE`` are supported, they allocate a 16 bit variable in
  RAM (``.data`` segment).

- The word ``INTERRUPT`` defines a new interrupt function. It takes the vector
  number from the stack and it expects that a function name follows. It creates
  symbols ``vector_NN`` which have to be manually added to the interrupt vector
  table. Interrupt declarations end with the word ``END-INTERRUPT``.

- Words defined using ``CODE``/``END-CODE`` are executed when cross compiling.
  They are expected to write out MSP430 assembler.

- ``INCLUDE`` loads and executes the given file. There is a search path that can
  be influenced with the ``-I`` command line option. Some files are built-in,
  e.g. ``core.forth`` is part of the package.

- Escapes are decoded in strings. e.g. ``." \n"`` outputs a newline.

- The ``DEPENDS-ON`` word can be used in ``CODE`` words. It adds the given
  word as dependency so that it is also cross compiled. This is useful when
  the assembler in the ``CODE`` words wants to use some shared code.


Internals
~~~~~~~~~

- SP is used as data stack.
- Interrupts and other asm/C functions called so then use the data stack.
- The return stack and instruction pointers are also kept in registers. All
  other registers can be used in Forth_ words (see generated assembler for
  register usage).

.. caution:: There is no stack depth checking implemented. Not maintaining the
             stack balance usually ends up in executing random parts or the
             program (A.K.A. "crash").


Limitations
-----------
The current language is not quite Forth_. Some important words such as
``DOES>`` are missing.

- Not ANS Forth compliant.

- The Forth_ interpreter only reads in words. There is no access to the
  characters of the source file and whitespace and newlines are discarded. So
  the strings ``." Hello World"`` and ``." Hello    World"`` are identical.
  Some words such as ``."`` partially emulate byte wise access by processing
  each word by character (that's why the closing ``"`` is detected in the
  previous examples).

- ``\`` Comments are not supported due to the limitation discussed above.

- ``*``, ``/``, ``/MOD`` are currently not available on the target.

- ``CREATE``, ``ALLOT`` have limited functionality.

- ``ERASE`` was named ``ZERO`` due to a naming conflict with a bit of the
  MSP430 Flash module.

- No double precision math.

- Input/output functions are missing.

- There are more...


Thanks
------
A number of core Forth_ words that are implemented in Forth_ itself are taken
from JonesForth_ (Licensed as Public Domain) which is a well documented
experimental Forth for x386 computers (used in
``msp430/asm/forth/__init__.forth``).

.. _JonesForth: http://git.annexia.org/?p=jonesforth.git;a=summary
.. _Forth: http://en.wikipedia.org/wiki/Forth_(programming_language)
