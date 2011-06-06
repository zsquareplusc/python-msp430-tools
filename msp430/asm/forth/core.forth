( vi:ft=forth )

: SPACE 32 EMIT ;
: HASH 35 EMIT ;
: NL 10 EMIT ;

: DEFINE HASH ." define " SPACE ;
: NEXT ." \t mov @IP+, PC ; NEXT \n " ;
: TOS->R15 ." \t mov @TOS+, R15 \n " ;
: TOS->R14 ." \t mov @TOS+, R14 \n " ;

CODE ABORT
    ." \t mov \x23 .param_stack_end, TOS \n "
    ." \t mov \x23 .return_stack_end, RTOS \n "
    ." \t mov \x23 thread, IP \n "
    NEXT
END-CODE

CODE LIT
    ." \t decd TOS \n
    \t mov @IP+, 0(TOS) \n "
    NEXT
END-CODE

CODE DOCOL
    ." \t decd RTOS \n
    \t mov IP, 0(RTOS) \n
    \t mov -2(IP), IP \n
    \t incd IP \n "
    NEXT
END-CODE

CODE EXIT
    ." \t mov @RTOS+, IP \n "
    NEXT
END-CODE

CODE BRANCH
    ." \t add @IP+, IP \n "
    NEXT
END-CODE

CODE BRANCH0
    ." \t mov @IP+, W \n
    \t tst 0(TOS) \n
    \t incd TOS \n
    \t jnz .Lnjmp \n
    \t add W, IP \n "
." .Lnjmp: "
    ." \t incd TOS \n "
    NEXT
END-CODE


( Generate a simple line for headers )
: LINE ( - )
    ." ; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - " NL
;

( Generate a header in the assembler file )
: HEADER ( s - )
    ." ;============================================================================ " NL
    ." ; " SPACE . NL ( print value from stack )
    ." ;============================================================================ " NL
;

( Generate init code for forth runtime and core words )
: CROSS-COMPILE-CORE ( - )
    LINE
    HASH ." include < " MCU . ." .h> " NL
    NL
    LINE
    ." ; Assign registers. \n "
    DEFINE ." TOS R4 " NL
    DEFINE ." RTOS  R5 " NL
    DEFINE ." IP  R6 " NL
    DEFINE ." W  R7 " NL
    NL
    LINE
    ." ; Memory for the stacks. \n "
    ." .bss \n "
    ." param_stack: .skip 2*32 \n "
    ." .param_stack_end:\n "
    ." return_stack: .skip 2*16 \n "
    ." .return_stack_end: \n "
    NL
    LINE
    ." ; Main entry point. \n "
    ." .text \n "
    ." main: \n "
        ." \t mov \x23 WDTPW|WDTHOLD, &WDTCTL \n "
        ." \t jmp ABORT \n "
    NL
    LINE
    ." ; Initial thread that is run. Hardcoded init-main-loop. \n "
    ." thread: \n "
    ." \t .word INIT \n "
    ." \t .word MAIN \n "
    ." \t .word ABORT \n "
    NL

    ( output important runtime core parts )
    CROSS-COMPILE ABORT
    CROSS-COMPILE LIT
    CROSS-COMPILE DOCOL
    CROSS-COMPILE EXIT
    CROSS-COMPILE BRANCH
    CROSS-COMPILE BRANCH0
;

( SHOW HEADER )
