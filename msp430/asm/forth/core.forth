( vi:ft=forth

  Core definitions for the cross compiler
  for Forth -> MSP430 assembler.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

INCLUDE _asm_snippets.forth

( > Terminate program and restart from the beginning.
( > The implementation is is also providing the 'main' entry point. )
CODE ABORT
    ." main: \t; also the main entry point.\n "
    ." \t mov \x23 _stack, SP \n "
    ." \t mov \x23 .return_stack_end, RTOS \n "
    ." \t mov \x23 thread, IP \n "
    ASM-NEXT
END-CODE

( > Internal helper to execute a thread of forth instructions. )
CODE DOCOL
    ." \t decd RTOS       \t; prepare to push on return stack \n "
    ." \t mov IP, 0(RTOS) \t; save IP on return stack \n "
    ." \t mov -2(IP), IP  \t; get where we are now \n "
   ( ." \t incd IP         \t; jump over 'jmp DOCOL' \n " )
    ." \t add \x23 4, IP  \t; jump over 'br HASH DOCOL' \n "
    ASM-NEXT
END-CODE

( > a.k.a return from subroutine. )
CODE EXIT
    ." \t mov @RTOS+, IP  \t; get last position from return stack \n "
    ASM-NEXT
END-CODE

( Get additional library functions. )
INCLUDE _builtins.forth
INCLUDE _memory.forth
INCLUDE _helpers.forth
INCLUDE _msp430_lowlevel.forth


( > Generate init code for forth runtime and core words. )
: CROSS-COMPILE-CORE ( - )
    LINE
    HASH ." include < " MCU . ." .h> " LF
    LF
    LINE
    ." ; Assign registers. \n "
    DEFINE ." RTOS  R4 \n "
    DEFINE ." IP  R5 \n "
    DEFINE ." W  R6 \n "
    LF
    LINE
    ." ; Memory for the return stack. \n "
    ." .bss \n "
    ." return_stack: .skip 2*16 \n "
    ." .return_stack_end: \n "
    LF
    LINE
    ." .text\n "
    ." ; Initial thread that is run. Hardcoded init-main-loop. \n "
    ." thread: \n "
    ." \t .word _INIT \n "
    ." \t .word _MAIN \n "
    ." \t .word _ABORT \n "
    LF

    ( output important runtime core parts )
    CROSS-COMPILE ABORT
    CROSS-COMPILE DOCOL
    CROSS-COMPILE EXIT
;

