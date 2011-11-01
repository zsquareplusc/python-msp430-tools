; Vector table with 64 bytes
; vi:ft=msp430

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
        .word  vector_30
        .word  vector_32
        .word  vector_34
        .word  vector_36
        .word  vector_38
        .word  vector_40
        .word  vector_42
        .word  vector_44
        .word  vector_46
        .word  vector_48
        .word  vector_50
        .word  vector_52
        .word  vector_54
        .word  vector_56
        .word  vector_58
        .word  vector_60
        .word  __RESET    ; POR


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
.weakalias vector_30, __unused_interrupt
.weakalias vector_32, __unused_interrupt
.weakalias vector_34, __unused_interrupt
.weakalias vector_36, __unused_interrupt
.weakalias vector_38, __unused_interrupt
.weakalias vector_40, __unused_interrupt
.weakalias vector_42, __unused_interrupt
.weakalias vector_44, __unused_interrupt
.weakalias vector_46, __unused_interrupt
.weakalias vector_48, __unused_interrupt
.weakalias vector_50, __unused_interrupt
.weakalias vector_52, __unused_interrupt
.weakalias vector_54, __unused_interrupt
.weakalias vector_56, __unused_interrupt
.weakalias vector_58, __unused_interrupt
.weakalias vector_60, __unused_interrupt
