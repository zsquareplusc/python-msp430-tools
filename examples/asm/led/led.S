; Test program for msp430.asm.as and msp430.asm.ld
;
; This one toggles the pin P1.1. This is like the LED flashing example that
; comes preprogrammed on some of the eval boards from TI.


.text
        ; entry point after device reset
RESET:  mov     #0x5a80, &0x120         ; disable WDT
        bis.b   #1, &0x22               ; set pin to output

        ; loop toggling the pin and then doing a delay
.L1:    xor.b   #1, &0x21               ; toggle pin
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

