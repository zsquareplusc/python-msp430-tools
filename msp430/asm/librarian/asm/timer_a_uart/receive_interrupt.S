; -*- coding: utf-8 -*-
; vi:ft=msp430
;
; DOC-SECTION
;
; Description
; -----------
; Timer UART implementation for reception.
;
; Receive characters in NRZ format. Timing is done with Timer module.
; Pin used for reception must be connected to the Timer. The user
; is responsible to configure the pin as input and module function
; (DIR=0, SEL=1).
;
; The Timer has to be set up for reception. The following function
; implements this:
;
; C Prototype: void timer_uart_rx_setup(void)
;
; To receive data, a function named TAUART_RX_INTERRUPT must be provided
; (using a #define to change the name is possible). This function must be
; an interrupt function and it can read the received byte from the
; variable timer_a_uart_rxd.
;
; Module configuration
; --------------------
; The module includes the file "hardware.h" which is expected to
; provide the following settings.
;
; The code uses the following #defines. When not defined defaults
; are used: TACCR1/TACCTL1, P1OUT/BIT3, 2400 baud for a timer at 1MHz
;
; TAUART_BIT_TICKS  Timer of a bit in timer ticks.
; TAUART_RX_TxR     Definition of the timer counter register.
; TAUART_RX_CCR     The capture compare unit used, its counter register.
; TAUART_RX_CCTL    The capture compare unit used, its control register.
;
;
; Copyright (c) 2001-2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
;
; END-DOC-SECTION

#include "hardware.h"

#ifndef TAUART_BIT_TICKS
    #define TAUART_BIT_TICKS    416 // ~2400 @ 1e6
#endif // TAUART_BIT_TICKS

#ifndef TAUART_RX_TxR
    #define TAUART_RX_TxR       TAR
#endif // TAUART_RX_TxR

#ifndef TAUART_RX_CCR
    #define TAUART_RX_CCR       TACCR1
#endif // TAUART_RX_CCR

#ifndef TAUART_RX_CCTL
    #define TAUART_RX_CCTL      TACCTL1
#endif // TAUART_RX_CCTL

#ifndef TAUART_VECTOR
    #define TAUART_VECTOR       TIMERA1_VECTOR
#endif // TAUART_VECTOR


; variables
.bss

timer_a_uart_rxd:
            .skip   1                   ; char var
.Lrxshift:  .skip   1                   ; char var
            .even
.Lrxbit:    .skip   2                   ; receive state counter

.text

; ---------------------------------------------------------------------------
; Interrupt handler to receive as Timer_A UART.
; Timer_A UART: receive character
; Resources: TACCR1
;
; x,8,N,1
; ___      ______________                     _______________
;    |    |              |                   |
;    | ST | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | SP |
;    |____|              |___________________|
;    ^       ^    ^    ^    ^    ^    ^    ^    ^     interrupts
;  Capture   |<------------ Compare ----------->|
; ---------------------------------------------------------------------------
__vector_{TAUART_VECTOR}:
timer_uart_interrupt:
        bic     #CCIFG, &TAUART_RX_CCTL ; clear interrupt flag
        add     .Lrxbit, PC
        jmp     .Lrxstart               ; start bit
        jmp     .Lrxdatabit             ; D0
        jmp     .Lrxdatabit             ; D1
        jmp     .Lrxdatabit             ; D2
        jmp     .Lrxdatabit             ; D3
        jmp     .Lrxdatabit             ; D4
        jmp     .Lrxdatabit             ; D5
        jmp     .Lrxdatabit             ; D6
;        jmp     .Lrxlastbit             ; D7 that one is following anyway

.Lrxlastbit:                            ; last bit, handle byte
        bit     #SCCI, &TAUART_RX_CCTL  ; read last bit
        rrc.b   .Lrxshift               ; and save it
        clr     .Lrxbit                 ; reset state
        mov     #CCIE|CAP|CM_2|CCIS_0|SCS, &TAUART_RX_CCTL ; restore capture mode
        mov.b   .Lrxshift, timer_a_uart_rxd  ; copy received data
        br      #TAUART_RX_INTERRUPT

.Lrxstart:                              ; start bit, initialize
        clr     .Lrxshift               ; clear input buffer
        add     #(TAUART_BIT_TICKS/2), &TAUART_RX_CCR   ; start bit + 1.5 bits -> first bit
        mov     #CCIE|CCIS_0|SCS, &TAUART_RX_CCTL       ; set compare mode, sample bits
        jmp     .Lrxex                  ; set state,...

.Lrxdatabit:                            ; save data bit
        bit     #SCCI, &TAUART_RX_CCTL  ; measure data bit
        rrc.b   .Lrxshift               ; rotate in data bit

.Lrxex: add     #TAUART_BIT_TICKS, &TAUART_RX_CCR ; one bit delay
        incd    .Lrxbit                 ; setup next state
        reti

; ---------------------------------------------------------------------------
; Set up for reception.
; ---------------------------------------------------------------------------
timer_uart_rx_setup:
        mov     #CCIE|CAP|CM_2|CCIS_0|SCS, &TAUART_RX_CCTL ; capture mode
        ret

