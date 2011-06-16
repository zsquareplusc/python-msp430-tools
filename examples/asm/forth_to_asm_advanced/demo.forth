( vi:ft=forth

  Serial input output [X-Protocol] Example.
  Hardware: Launchpad
  Serial Port Settings: 2400,8,N,1

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
INCLUDE core.forth
INCLUDE msp430.forth
INCLUDE io.forth

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )

CODE WRITE
    TOS->R15
    ." \t call \x23 write\n "
    ASM-NEXT
END-CODE

CODE EMIT
    TOS->R15
    ." \t call \x23 putchar\n "
    ASM-NEXT
END-CODE

CODE TIMER_A_UART_INIT
    ." \t call \x23 timer_uart_rx_setup\n "
    ASM-NEXT
END-CODE


CODE RX-CHAR
    ." \t mov.b timer_a_uart_rxd, W\n "
    ." \t push W\n "
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Control the LEDs on the Launchpad )
: RED_ON    BIT0 P1OUT CSET ;
: RED_OFF   BIT0 P1OUT CRESET ;
: GREEN_ON  BIT6 P1OUT CSET ;
: GREEN_OFF BIT6 P1OUT CRESET ;

( Read in the button on the Launchpad )
: S2        P1IN C@ BIT3 AND NOT ;

( Delay functions )
: SHORT-DELAY     0x4fff DELAY ;
: LONG-DELAY      0xffff DELAY ;
: VERY-LONG-DELAY LONG-DELAY LONG-DELAY ;
( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Simple event handler. A bit field is used to keep track of events. )
VARIABLE EVENTS
( Bit masks for the individual events )
BIT0 CONSTANT KEY-EVENT
BIT1 CONSTANT TIMER-EVENT
BIT2 CONSTANT RX-EVENT

( ------ Helper functions ------ )
( Start an event )
: START EVENTS CSET ;
( Test if event was started. Reset its flag anyway and return true when it was set. )
: PENDING?
    DUP                 ( copy bit mask )
    EVENTS CTESTBIT IF  ( test if bit is set )
        EVENTS CRESET   ( it is, reset )
        TRUE            ( indicate true as return value )
    ELSE
        DROP            ( drop bit mask )
        FALSE           ( indicate false as return value )
    ENDIF
;
( Return true if no events are pending )
: IDLE?
    EVENTS C@ 0=
;
( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )

( Interrupt handler for P1 )
PORT1_VECTOR INTERRUPT P1-IRQ-HANDLER
    KEY-EVENT START     ( Set event flag for key )
    WAKEUP              ( terminate LPM modes )
    0 P1IFG C!          ( clear all interrupt flags )
END-INTERRUPT

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )

( Watchdog interrupts with SMCLK = 1MHz are too fast for us.
  Only wakeup every n-th interrupt. This is the counter
  used to achieve this. )
VARIABLE SLOWDOWN

( Interrupt handler for Watchdog module in timer mode )
WDT_VECTOR INTERRUPT WATCHDOG-TIMER-HANDLER
    SLOWDOWN C@ 1 +     ( get and increment counter )
    DUP 30 > IF         ( check value )
        TIMER-EVENT START ( set event flag for timer )
        WAKEUP          ( terminate LPM modes )
        DROP 0          ( reset counter )
    ENDIF
    SLOWDOWN C!         ( store new value )
END-INTERRUPT

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )

( Received data is put into a small line buffer. When a newline
  is received processing in the foreground is started.
)
0 VALUE RX-POS
RAM CREATE RX-BUFFER 8 ALLOT

100 INTERRUPT TAUART_RX_INTERRUPT
    RX-CHAR DUP             ( get the received character )
    RX-BUFFER RX-POS + C!   ( store character )
    RX-POS 7 < IF           ( increment write pos if there is space )
        RX-POS 1 + TO RX-POS
    ENDIF
    '\n' = IF               ( check for EOL )
        RX-EVENT START      ( set event flag for reception )
        WAKEUP              ( terminate LPM modes )
        0 TO RX-POS         ( reset read position )
    ENDIF
END-INTERRUPT

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Initializations run after reset )
: INIT ( -- )
    ( Initialize pins )
    OUT TACCTL0 !       ( Init Timer A CCTL before pin is activated DIR, SEL)
    BIT1 P1OUT C!       ( TXD )
    [ BIT1 BIT2 + ] LITERAL P1SEL C! ( TXD RXD )
    [ BIT0 BIT1 + BIT6 + ] LITERAL P1DIR C!
    BIT3 P1IES C!       ( select neg edge )
    0 P1IFG C!          ( reset flags )
    BIT3 P1IE C!        ( enable interrupts for S2 )

    ( Use Watchdog module as timer )
    [ WDTPW WDTTMSEL + ] LITERAL WDTCTL !
    WDTIE IE1 C!

    ( Initialize clock from calibration values )
    CALDCO_1MHZ DCOCTL  C@!
    CALBC1_1MHZ BCSCTL1 C@!

    ( Set up Timer A - used for UART )
    [ TASSEL1 MC1 + ] LITERAL TACTL !
    TIMER_A_UART_INIT

    ( Indicate startup with LED )
    GREEN_ON
    VERY-LONG-DELAY
    GREEN_OFF

    ( Enable interrupts now )
    EINT
;

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )

( Output OK message )
: XOK ( -- )  ." xOK\n" ;


( Output one hex digit for the number on the stack )
: .HEXDIGIT ( u - )
    0xf AND DUP 10 >= IF [ 'A' 10 - ] LITERAL ELSE '0' ENDIF + EMIT
;

( Output two hex digits for the byte on the stack )
: .HEX ( u -- )
    DUP
    4 RSHIFT .HEXDIGIT
    .HEXDIGIT
;


( Main application, run after INIT )
: MAIN ( -- )
    BEGIN
        ( Test if events are pending )
        IDLE? IF
            ( XXX actually we could miss an event and go to sleep if it was set
                  between test and LPM. The event flag is not lost, but it is
                  executed later when some other event wakes up the CPU. )
            ( Wait in low power mode )
            ENTER-LPM0
        ENDIF
        ( After wakeup test for the different events )

        RX-EVENT PENDING? IF
            GREEN_ON    ( Show activity )
            ( RX-CHAR EMIT ( send echo )
            RX-BUFFER C@ CASE
                [CHAR] s OF         ( read switch command )
                    [CHAR] i EMIT
                    ( return state of button )
                    S2 IF [CHAR] 1 ELSE [CHAR] 0 ENDIF EMIT
                    '\n' EMIT
                    XOK
                ENDOF
                [CHAR] o OF         ( output a message )
                    RX-BUFFER WRITE
                    XOK
                ENDOF
                [CHAR] m OF         ( memory dump )
                    [CHAR] h EMIT
                    0x10c0   ( XXX read start address and range from command )
                    ( hex dump of INFOMEM segment with calibration values )
                    BEGIN
                        DUP 0x10ff <=   ( end address not yet reached )
                    WHILE
                        DUP C@ .HEX     ( hex dump of address )
                        1+              ( next address )
                    REPEAT
                    DROP ." \n"         ( finish hex dump, drop address on stack )
                    XOK
                ENDOF
                ( default )
                ." xERR unknown command: "
                RX-BUFFER WRITE
            ENDCASE
            RX-BUFFER 8 ZERO            ( erase buffer for next round )
            GREEN_OFF                   ( Activity done )
        ENDIF

        KEY-EVENT PENDING? IF
            ( Green flashing  )
            GREEN_ON
            SHORT-DELAY
            GREEN_OFF
        ENDIF

        TIMER-EVENT PENDING? IF
            ( Red flashing )
            RED_ON
            SHORT-DELAY
            RED_OFF
        ENDIF
(        S2 IF
        ELSE
        ENDIF
)
    AGAIN
;

( ========================================================================= )
( Generate the assembler file now )
" Advanced demo " HEADER

( output important runtime core parts )
" Core " HEADER
CROSS-COMPILE-CORE

( cross compile application )
" Application " HEADER
CROSS-COMPILE-VARIABLES
CROSS-COMPILE INIT
CROSS-COMPILE MAIN
CROSS-COMPILE P1-IRQ-HANDLER
CROSS-COMPILE WATCHDOG-TIMER-HANDLER
CROSS-COMPILE TAUART_RX_INTERRUPT
CROSS-COMPILE-MISSING ( This compiles all words that were used indirectly )
