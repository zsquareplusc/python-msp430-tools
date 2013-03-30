; Test program for msp430.asm.cpp, msp430.asm.as and msp430.asm.ld
;
; This one toggles the pin P1.0. This is like the LED flashing example that
; comes preprogrammed on some of the eval boards from TI.


.text
        ; entry point after device reset
RESET:  mov     #0x5a80, &0x015c        ; disable WDT
        bis.b   #1, &0x0204             ; set pin to output
        bra     #.L1                    ; go to the main loop

; just for fun, place the main loop in the upper flash memory
.section FLASH2
        ; loop toggling the pin and then doing a delay
.L1:    xor.b   #1, &0x0202             ; toggle pin
        mov     #0xc350, R15            ; init delay loop
.L2:    dec     R15                     ; count down
        jnz     .L2                     ; jump while counter is not zero
        jmp     .L1                     ; loop the toggling part


; set the reset vector to the program start
.section .vectors
        .skip  126                      ; skip other vectors
        .word  RESET                    ; reset vector

