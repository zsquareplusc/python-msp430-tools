; -*- coding: utf-8 -*-
; vi:ft=msp430
;
; DOC-SECTION
;
; Description
; -----------
; Write a null terminated string using putchar.
;
; C prototype:  void write(const char *s);
; Parameter s: Null terminated message
;
; Copyright (c) 2001-2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
;
; END-DOC-SECTION

.text
; ---------------------------------------------------------------------------
; Write a null terminated string using the putchar function.
; R15: pointer to null terminated text
; ---------------------------------------------------------------------------
write:
        mov     R15, R14        ; copy pointer
.Lwrite_loop:
        mov.b   @R14+, R15      ; fetch character
        tst     R15             ; test for null character
        jz      .Lwrite_fini    ; exit loop on null char
        call    #putchar        ; output character
        jmp     .Lwrite_loop    ; loop
.Lwrite_fini:
        ret

