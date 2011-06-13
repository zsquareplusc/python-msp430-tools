; -*- coding: utf-8 -*-
; vi:ft=msp430
;
; DOC-SECTION
;
; Description
; -----------
; Timer UART implementation of putchar.
;
; C prototype:  int putchar(int c);
; Paramter c: Character to send (0..255)
; Returns: >= 0 on success
;
; Transmit characters in NRZ format, 8 bits, 1 stop bit, no parity.
; Timing is done with Timer module, signal is generated with OUTMOD.
; The user has to ensure that the corresponding pins are configured
; for module function (DIR=1, SEL=1).
;
; Compared to the putchar version that directly accesses a GPIO has
; this version the advantage that it is more robust when other
; interrupts run in parallel. Its drawback is that the selection of
; pins is restricted to pin connected to the timer.
;
; Module configuration
; --------------------
; The module includes the file "hardware.h" which can be used to
; provide the following settings.
;
; The code uses the following #defines. When not defined defaults
; are used: TACCR0/TACCTL0, P1OUT/BIT2, 2400 baud for a timer at 1MHz
;
; TAUART_BIT_TICKS
;   Timer of a bit in timer ticks.
;
; TAUART_TX_TxR
;   Definition of the timer counter register.
;
; TAUART_TX_CCR
;   The capture compare unit used, its counter register.
;
; TAUART_TX_CCTL
;   The capture compare unit used, its control register.
;
; TAUART_TX_DINT
;    If defined: lock interrupts during send. This ensures that
;    no other interrupt can disturb the bit timing. But it also
;    prevents full duplex mode.
;
; Copyright (c) 2001-2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
;
; END-DOC-SECTION

#include "hardware.h"

#ifndef TAUART_BIT_TICKS
    #define TAUART_BIT_TICKS  416 // ~2400 @ 1e6
#endif // TAUART_BIT_TICKS

#ifndef TAUART_TX_TxR
    #define TAUART_TX_TxR      TAR
#endif // TAUART_TX_TxR

#ifndef TAUART_TX_CCR
    #define TAUART_TX_CCR      TACCR0
#endif // TAUART_TX_CCR

#ifndef TAUART_TX_CCTL
    #define TAUART_TX_CCTL     TACCTL0
#endif // TAUART_TX_CCTL

.text
; ---------------------------------------------------------------------------
; Timer_A UART: send character
; Parameters: R15 character to be sent
; Resources: TACCR0, R13
;
; x,8,N,1
; ___      ______________                     _______________
;    |    |              |                   |
;    | ST | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | SP |
;    |____|              |___________________|
;    ^    ^    ^    ^    ^    ^    ^    ^    ^    ^    edges
;
; ---------------------------------------------------------------------------
putchar:
        mov     #10, R13                        ; ten bits: Start, 8 Data, Stop
        rla     R15                             ; shift in start bit (0)
#ifdef TAUART_TX_DINT
        push    SR
        dint
#endif // TAUART_TX_DINT
        bis     #0x0600, R15                    ; set 10th bit (STOP) and the next to get a return value of 1
        mov     &TAUART_TX_TxR, &TAUART_TX_CCR  ; copy current time
.Lt1lp: rra     R15                             ; | shift data through carry
        jc      .Lt1                            ; | test carry bit
.Lt0:   mov     #OUTMOD_5, &TAUART_TX_CCTL      ; |
        jmp     .Ltc                            ; |
.Lt1:   mov     #OUTMOD_1, &TAUART_TX_CCTL      ; |
        jmp     .Ltc                            ; |
.Ltc:   add     #TAUART_BIT_TICKS, &TAUART_TX_CCR;| set up one bit delay
.Ltcd:  bit     #CCIFG, &TAUART_TX_CCTL         ; | \ time due?         ] delay
        jz      .Ltcd                           ; | / not yet -> loop   ]
        dec     R13                             ; | decrement bit counter
        jnz     .Lt1lp                          ; O loop until all bits are transmitted
#ifdef TAUART_TX_DINT
        pop     SR
#endif // TAUART_TX_DINT
        ret

