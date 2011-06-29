; Example for MSP430G2 Launchpad kit
;
; Some value line MCUs have only the 1MHz clock calibration value programmed.
; This tool uses this value to calibrate 8, 12 and 16 MHz.
;
; NOTES:
; - VLOCLK varies from 4..20kHz (250..50us)
; - ACLK=VLOCLK is divided by 8 -> 2000...400us
; - For 16MHz we sum up 16 times the pulse width -> 32000...6400 us
; - a timer tick is 1MHz for the measurement, so this fits well into 16 bits
;
; Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
#include <msp430.h>


;~ #define FREQ_MHZ     1              // target frequency in MHz
;~ #define FREQ_MHZ     4              // target frequency in MHz
#define FREQ_MHZ     8              // target frequency in MHz
;~ #define FREQ_MHZ    12              // target frequency in MHz
;~ #define FREQ_MHZ    16              // target frequency in MHz

.text
        ; entry point after device reset
RESET:  mov     #WDTPW|WDTHOLD, &WDTCTL ; disable WDT
        ; init clock to 1MHz from calibration values
        mov.b   CALDCO_1MHZ, &DCOCTL
        mov.b   CALBC1_1MHZ, &BCSCTL1
        mov.b   #LFXT1S_2, &BCSCTL3     ; select VLOCLK on ACLK
        ;~ bis.b   #DIVA_3, &BCSCTL1       ; divide ACLK by 8
        bis.b   #DIVA_1, &BCSCTL1       ; divide ACLK by 2
        ; init ports
        clr.b   &P1OUT                  ; clear pins
        mov.b   #BIT4, &P1SEL           ; enable SMCLK on P1.4
        ;~ mov.b   #BIT0|BIT4, &P1SEL           ; enable SMCLK on P1.4, ACLK on P1.0
        mov.b   #BIT0|BIT4|BIT6, &P1DIR ; set SMCLK as output, LEDs
        ; start timer
        mov     #TASSEL_2|MC_2, &TACTL  ; SMCLK, continuous mode
        mov     #CCIS_1|CM0|CAP, &TACCTL0 ; select ACLK as input, capture mode

; ---------------------------------------------------------------------------
; Measure ACLK
measure_aclk:
        mov     #FREQ_MHZ, R13          ; number of rounds, e.g. 16 for 16MHz
        clr     R15                     ; prepare result
        ; wait until CCIFG flag is set
        bic     #CCIFG, &TACCTL0        ; clear bit
.Lmw1:  bit     #CCIFG, &TACCTL0        ; test bit
        jz      .Lmw1                   ; not set -> loop
        mov     &TACCR0, R14
        ; then measure cycles (wait again until CCIFG is set)
.Lmlp:  bic     #CCIFG, &TACCTL0        ; clear bit
.Lmw2:  bit     #CCIFG, &TACCTL0        ; test bit
        jz      .Lmw2                   ; not set -> loop
        mov     &TACCR0, R12            ; calculate difference
        sub     R14, R12
        add     R12, R15                ; sum up ticks per rounds
        mov     &TACCR0, R14            ; get counter value for next round
        ; loop until the number of desired rounds are summed up
        dec     R13
        jnz     .Lmlp
        mov     R15, 0x0200             ; keep result

; ---------------------------------------------------------------------------
; Run FLL code
        mov     256*16, R5
fll_adjust:
        dec     R5
        jz      fail

        ; Wait until capture occured!
        bic     #CCIFG, &TACCTL0        ; clear bit
.Lfll1: bit     #CCIFG, &TACCTL0        ; test bit
        jz      .Lfll1                  ; not set -> loop
        mov     &TACCR0, R14            ; get counter value for next round

        bic     #CCIFG, &TACCTL0        ; clear bit
.Lfll2: bit     #CCIFG, &TACCTL0        ; test bit
        jz      .Lfll2                  ; not set -> loop
        mov     &TACCR0, R12            ; calculate difference
        sub     R14, R12
        mov     R12, 0x0202             ; keep result

        ; compare measured value against desired value
        cmp     R15, R12
        jeq     .Lffl_ok                ; if equal, desired frequency is set -> exit
        jnc     .Lfllinc                ; DCO is too slow
.Lflldec:
        dec.b   &DCOCTL                 ; DCO is to fast
        jnc     fll_adjust              ; did DCO roll under? jump if not
        bit.b   #RSEL0|RSEL1|RSEL2|RSEL3, &BCSCTL1
        jz      fail                    ; lower boundary hit -> failure
        dec.b   &BCSCTL1                ; select next lower RSEL
        jmp     fll_adjust
.Lfllinc:
        inc.b   &DCOCTL                 ; DCO is too slow
        jnc     fll_adjust              ; did DCO roll over? jump if not
        mov.b   &BCSCTL1, R6
        and.b   #RSEL0|RSEL1|RSEL2|RSEL3, R6
        cmp.b   #RSEL0|RSEL1|RSEL2|RSEL3, R6
        jeq     fail                    ; upper boundary hit -> failure
        inc.b   &BCSCTL1                ; select next lower RSEL
        jmp     fll_adjust
.Lffl_ok:
        jmp     ok

; ---------------------------------------------------------------------------
; XXX only write when values are not already valid

fail:   mov     #BIT0, R4               ; enable RED LED
        jmp     .L1
ok:     mov     #BIT6, R4               ; enable GREEN LED
        ; loop toggling the pin and then doing a delay
.L1:    xor.b   R4, &P1OUT              ; toggle pin
        mov     #163, R15               ; init delay loop for toggling at 1kHz @ 1MHz (500us)
        ;~ mov     #0xc350, R15            ; init delay loop
.L2:    dec     R15                     ; count down
        jnz     .L2                     ; jump while counter is not zero
        jmp     .L1                     ; loop the toggling part


; ---------------------------------------------------------------------------
; set the reset vector (and all the others) to the program start
.section .vectors
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET                    ; reset vector

; vim: set ft=msp430:
