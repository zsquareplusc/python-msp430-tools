( LED flashing example
  Hardware: Lauchpad

  vi:ft=forth
)

INCLUDE msp430.forth
INCLUDE core.forth

CODE @B
    TOS->R15
    ." \t mov.b @R15, 0(TOS) " NL
    NEXT
END-CODE

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
(    10 12 >
    IF 10 ELSE 20 ENDIF
    DROP
)
;

CODE DELAY
    TOS->R15
    ." .loop: \t dec R15 \n "
    ." \t jnz .loop \n "
    NEXT
END-CODE

( Control the LEDs on the Launchpad )
: RED_ON    P1OUT BIT0 BIT_SET_BYTE ;
: RED_OFF   P1OUT BIT0 BIT_CLEAR_BYTE ;
: GREEN_ON  P1OUT BIT6 BIT_SET_BYTE ;
: GREEN_OFF P1OUT BIT6 BIT_CLEAR_BYTE ;

( Read in the button on the Launchpad )
: S2        P1IN  @B BIT3 & NOT ;

: MAIN
    BEGIN
        ( Red flashing )
        RED_ON
        0xffff DELAY
        RED_OFF
        0xffff DELAY

        ( Green flashing if button is pressed )
        S2 IF
            GREEN_ON
            0x4fff DELAY
            GREEN_OFF
            0x4fff DELAY
        ENDIF
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
