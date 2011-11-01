; Vector table with 32 bytes
; vi:ft=msp430

; Interrupt table
.section .vectors
        .word  __vector_0
        .word  __vector_2
        .word  __vector_4
        .word  __vector_6
        .word  __vector_8
        .word  __vector_10
        .word  __vector_12
        .word  __vector_14
        .word  __vector_16
        .word  __vector_18
        .word  __vector_20
        .word  __vector_22
        .word  __vector_24
        .word  __vector_26
        .word  __vector_28
        .word  __RESET    ; POR
        ;~ .word  vector_30    ; POR

.text
; Implementation for unused interrupts
__unused_interrupt: reti

; Assign __unused_interrupt to all vectors. As it is only a default, it is
; possible to provide different values/implementations for each vector.
.weakalias __vector_0,  __unused_interrupt
.weakalias __vector_2,  __unused_interrupt
.weakalias __vector_4,  __unused_interrupt
.weakalias __vector_6,  __unused_interrupt
.weakalias __vector_8,  __unused_interrupt
.weakalias __vector_10, __unused_interrupt
.weakalias __vector_12, __unused_interrupt
.weakalias __vector_14, __unused_interrupt
.weakalias __vector_16, __unused_interrupt
.weakalias __vector_18, __unused_interrupt
.weakalias __vector_20, __unused_interrupt
.weakalias __vector_22, __unused_interrupt
.weakalias __vector_24, __unused_interrupt
.weakalias __vector_26, __unused_interrupt
.weakalias __vector_28, __unused_interrupt
