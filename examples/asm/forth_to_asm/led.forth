( LED flashing example
  Hardware: Launchpad

  vi:ft=forth
)

INCLUDE msp430.forth
INCLUDE core.forth

CODE BIT_CLEAR_BYTE
    TOS->R15
    TOS->R14
    ." \t bic.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE BIT_SET_BYTE
    TOS->R15
    TOS->R14
    ." \t bis.b R14, 0(R15) " NL
    NEXT
END-CODE

( Control the LEDs on the Launchpad )
: RED_ON    BIT0 P1OUT BIT_SET_BYTE ;
: RED_OFF   BIT0 P1OUT BIT_CLEAR_BYTE ;
: GREEN_ON  BIT6 P1OUT BIT_SET_BYTE ;
: GREEN_OFF BIT6 P1OUT BIT_CLEAR_BYTE ;

( Read in the button on the Launchpad )
: S2        P1IN  C@ BIT3 & NOT ;


CODE DELAY
    TOS->R15
    ." .loop: \t dec R15 \n "
    ." \t jnz .loop \n "
    NEXT
END-CODE

: SHORT-DELAY 0x4fff DELAY ;
: LONG-DELAY 0xffff DELAY ;
: VERY-LONG-DELAY LONG-DELAY LONG-DELAY ;

: INIT
    [ BIT0 BIT6 + ] LITERAL P1DIR C!
    0 P1OUT C!
    GREEN_ON
    VERY-LONG-DELAY
    GREEN_OFF
    VERY-LONG-DELAY
    VERY-LONG-DELAY
;

: MAIN
    BEGIN
        ( Red flashing )
        RED_ON
        LONG-DELAY
        RED_OFF
        LONG-DELAY

        ( Green flashing if button is pressed )
        S2 IF
            GREEN_ON
            SHORT-DELAY
            GREEN_OFF
            SHORT-DELAY
        ENDIF
    AGAIN
;

( ========================================================================= )
( Generate the assembler file now )
" LED example " HEADER

( output important runtime core parts )
" Core " HEADER
CROSS-COMPILE-CORE

( cross compile application )
" Application " HEADER
CROSS-COMPILE-VARIABLES
CROSS-COMPILE INIT
CROSS-COMPILE MAIN
CROSS-COMPILE-MISSING
