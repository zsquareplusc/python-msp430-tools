; startup code. it initializes:
; - .data and .bss sections
; - stack pointer
; vi:ft=msp430

.text

RESET:      mov    #_stack, SP

.Linit_data:
            mov     #_data_init_end-_data_init_start, R15
            tst     R15
            jz      .Linit_bss
.Ldata_loop: dec     R15
            mov     _data_init_start(R15), _data_start(R15)
            jnz     .Ldata_loop

.Linit_bss:
            mov     #_bss_end-_bss_start, R15
            tst     R15
            jz      .Lrun
.Lbss_loop:  dec     R15
            clr     _bss_start(R15)
            jnz     .Lbss_loop

.Lrun:       br     #main

