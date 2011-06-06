( vi:ft=forth )

INCLUDE msp430.forth
INCLUDE core.forth

CODE !B
    TOS->R14
    TOS->R15
    ." \t mov.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE BIT_CLEAR_BYTE
    TOS->R14
    TOS->R15
    ." \t bic.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE BIT_SET_BYTE
    TOS->R14
    TOS->R15
    ." \t bis.b R14, 0(R15) " NL
    NEXT
END-CODE

: INIT
    P1DIR [ BIT0 BIT6 + LITERAL ] !B
    P1OUT 0 !B
    0 IF 10 ELSE 20 ENDIF
;

CODE DELAY
    TOS->R15
    ." .loop: \t dec R15 \n "
    ." \t jnz .loop \n "
    NEXT
END-CODE

: RED_ON    P1OUT BIT0 BIT_SET_BYTE ;
: RED_OFF   P1OUT BIT0 BIT_CLEAR_BYTE ;
: GREEN_ON  P1OUT BIT6 BIT_SET_BYTE ;
: GREEN_OFF P1OUT BIT6 BIT_CLEAR_BYTE ;

: MAIN
    BEGIN
        RED_ON
        0xffff DELAY
        RED_OFF
        0xffff DELAY
        GREEN_ON
        0x4fff DELAY
        GREEN_OFF
        0x4fff DELAY
    LOOP
;

( ========================================================================= )
( Generate the assembler file now )
" LED example " HEADER

( output important runtime core parts )
" Core " HEADER
CROSS-COMPILE-CORE

( cross compile application )
" Application " HEADER
CROSS-COMPILE INIT
CROSS-COMPILE MAIN
CROSS-COMPILE-MISSING
