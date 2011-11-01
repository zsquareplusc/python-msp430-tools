( LED flashing example
  Hardware: Launchpad

  vi:ft=forth
)

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
INCLUDE core.forth
INCLUDE msp430.forth

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Control the LEDs on the Launchpad )
: RED_ON    BIT0 P1OUT CSET ;
: RED_OFF   BIT0 P1OUT CRESET ;
: GREEN_ON  BIT6 P1OUT CSET ;
: GREEN_OFF BIT6 P1OUT CRESET ;

( Read in the button on the Launchpad )
: S2        BIT3 P1IN CTESTBIT NOT ;

( Delay functions )
: SHORT-DELAY     0x4fff DELAY ;
: LONG-DELAY      0xffff DELAY ;
: VERY-LONG-DELAY LONG-DELAY LONG-DELAY ;

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Initializations run after reset )
: INIT ( - )
    ( Initialize pins )
    0 P1OUT C!
    [ BIT0 BIT6 + ] LITERAL P1DIR C!
    ( Stop Watchdog module )
    [ WDTPW WDTHOLD + ] LITERAL WDTCTL !

    ( Initialize clock from calibration values )
    CALDCO_1MHZ DCOCTL  C@!
    CALBC1_1MHZ BCSCTL1 C@!

    ( Indicate startup with LED )
    GREEN_ON
    VERY-LONG-DELAY
    GREEN_OFF
    VERY-LONG-DELAY
    VERY-LONG-DELAY
;

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Main application, run after INIT )
: MAIN ( - )
    BEGIN
        S2 IF
            ( Green flashing if button is pressed )
            GREEN_ON
            SHORT-DELAY
            GREEN_OFF
            SHORT-DELAY
        ELSE
            ( Red flashing )
            RED_ON
            LONG-DELAY
            RED_OFF
            LONG-DELAY
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
CROSS-COMPILE-MISSING ( This compiles all words that were used indirectly )
