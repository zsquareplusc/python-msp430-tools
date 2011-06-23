; Example for MSP430G2 Launchpad kit
;
; This one toggles the pin P1.0.
; Clock is initialized from calibration values

.text
        ; entry point after device reset
RESET:  mov     #WDTPW|WDTHOLD, &WDTCTL ; disable WDT
        ; init clock to 1MHz from calibration values
        mov.b   CALDCO_1MHZ, &DCOCTL
        mov.b   CALBC1_1MHZ, &BCSCTL1
        ; init ports
        bis.b   #BIT0, &P1DIR           ; set pin to output

        ; loop toggling the pin and then doing a delay
.L1:    xor.b   #BIT0, &P1OUT           ; toggle pin
        mov     #0xc350, R15            ; init delay loop
.L2:    dec     R15                     ; count down
        jnz     .L2                     ; jump while counter is not zero
        jmp     .L1                     ; loop the toggling part


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
