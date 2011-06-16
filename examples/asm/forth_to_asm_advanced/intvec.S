; vi:ft=msp430
.section .vectors
        .word  RESET
        .word  RESET
        .word  vector_4 ; PORT1
        .word  RESET    ; PORT2
        .word  RESET    ; USI
        .word  RESET    ; ADC10
        .word  RESET
        .word  RESET
        .word  timer_uart_rx_interrupt  ; TACCR1
        .word  RESET    ; TACCR0
        .word  vector_20  ; WDT
        .word  RESET
        .word  RESET
        .word  RESET
        .word  RESET    ; NMI
        .word  RESET    ; POR

