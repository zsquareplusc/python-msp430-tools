; Vector table with 32 bytes
; vi:ft=msp430

; Interrupt table
.section .vectors
        .word  vector_0
        .word  vector_2
        .word  vector_4
        .word  vector_6
        .word  vector_8
        .word  vector_10
        .word  vector_12
        .word  vector_14
        .word  vector_16
        .word  vector_18
        .word  vector_20
        .word  vector_22
        .word  vector_24
        .word  vector_26
        .word  vector_28
        .word  __RESET    ; POR
        ;~ .word  vector_30    ; POR

.text
; Implementation for unused interrupts
__unused_interrupt: reti

; Assign __unused_interrupt to all vectors. As it is only a default, it is
; possible to provide different values/implementations for each vector.
.weakalias vector_0,  __unused_interrupt
.weakalias vector_2,  __unused_interrupt
.weakalias vector_4,  __unused_interrupt
.weakalias vector_6,  __unused_interrupt
.weakalias vector_8,  __unused_interrupt
.weakalias vector_10, __unused_interrupt
.weakalias vector_12, __unused_interrupt
.weakalias vector_14, __unused_interrupt
.weakalias vector_16, __unused_interrupt
.weakalias vector_18, __unused_interrupt
.weakalias vector_20, __unused_interrupt
.weakalias vector_22, __unused_interrupt
.weakalias vector_24, __unused_interrupt
.weakalias vector_26, __unused_interrupt
.weakalias vector_28, __unused_interrupt
