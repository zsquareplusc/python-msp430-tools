; -*- coding: utf-8 -*-
; vi:ft=msp430
;
; DOC-SECTION
;
; Description
; -----------
; Startup code. It initializes:
; - stack pointer
; - .data and .bss sections
;
; Copyright (c) 2001-2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
;
; END-DOC-SECTION

.text

            ; Initialize stack pointer
__RESET:    mov    #_stack, SP

.Linit_data: ; Copy initial values for variables in data segment
            mov     #_data_init_end-_data_init_start, R15
            tst     R15
            jz      .Linit_bss
.Ldata_loop:dec     R15
            mov     _data_init_start(R15), _data_start(R15)
            jnz     .Ldata_loop

.Linit_bss: ; Clear memory of bss segment
            mov     #_bss_end-_bss_start, R15
            tst     R15
            jz      .Lrun
.Lbss_loop: dec     R15
            clr     _bss_start(R15)
            jnz     .Lbss_loop

.Lrun:       br     #main

