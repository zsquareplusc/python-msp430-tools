; -*- coding: utf-8 -*-
; vi:ft=msp430
;
; DOC-SECTION
;
; Description
; -----------
; The single_adc10 function enabled the ADC10 module, makes a measurement and
; switched the module off.
;
; C prototype:  unsigned single_adc10(unsigned channel);
; Parameter channel: channel number
; Return: ADC measurement
;
; Module configuration
; --------------------
; The module includes the file "hardware.h" which can be used to
; provide the following settings.
;
; Copyright (c) 2011 Chris Liechti <cliechti@gmx.net>
; All Rights Reserved.
; Simplified BSD License (see LICENSE.txt for full text)
;
; END-DOC-SECTION
#include "hardware.h"

.text
; ---------------------------------------------------------------------------
; Perform a single ADC10 measurement.
; R15: input channel
; ---------------------------------------------------------------------------
single_adc10:
        mov     R15, &ADC10CTL1             ; get settings from R15
        mov     #ADC10SHT_3|ADC10ON, &ADC10CTL0     ; enable ADC10 module
        ;~ mov.b   R15, &ADC10AE0              ; enable input
        bis     #ENC|ADC10SC, &ADC10CTL0    ; Start sampling
.L1:    bit     #ADC10BUSY, &ADC10CTL1      ; test if ADC10 is busy
        jnz     .L1                         ; bit set? -> loop
        mov     &ADC10MEM, R15              ; get result in register
        clr     &ADC10CTL0
        ;~ clr.b   &ADC10AE0
        ret

