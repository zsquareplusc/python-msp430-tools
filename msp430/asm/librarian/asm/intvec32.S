; Vector table with 64 bytes
; vi:ft=msp430

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
        .word  __vector_30
        .word  __vector_32
        .word  __vector_34
        .word  __vector_36
        .word  __vector_38
        .word  __vector_40
        .word  __vector_42
        .word  __vector_44
        .word  __vector_46
        .word  __vector_48
        .word  __vector_50
        .word  __vector_52
        .word  __vector_54
        .word  __vector_56
        .word  __vector_58
        .word  __vector_60
        .word  __RESET    ; POR


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
.weakalias __vector_30, __unused_interrupt
.weakalias __vector_32, __unused_interrupt
.weakalias __vector_34, __unused_interrupt
.weakalias __vector_36, __unused_interrupt
.weakalias __vector_38, __unused_interrupt
.weakalias __vector_40, __unused_interrupt
.weakalias __vector_42, __unused_interrupt
.weakalias __vector_44, __unused_interrupt
.weakalias __vector_46, __unused_interrupt
.weakalias __vector_48, __unused_interrupt
.weakalias __vector_50, __unused_interrupt
.weakalias __vector_52, __unused_interrupt
.weakalias __vector_54, __unused_interrupt
.weakalias __vector_56, __unused_interrupt
.weakalias __vector_58, __unused_interrupt
.weakalias __vector_60, __unused_interrupt
