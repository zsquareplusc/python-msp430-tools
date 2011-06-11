( Words to work with interrupts.

  vi:ft=forth
)

( Example:
    PORT1_VECTOR INTERRUPT handler_name
        WAKEUP
        0 P1IFG C!
    END-INTERRUPT

  - Words defined with INTERRUPT must not be called from user code.
)

( Interrupts save the MSP430 context [registers] on the data stack. This is no
  problem as an interrupt handler can work with values that have been on the
  stack and it must be stack balanced itself.
)

( The word INTERRUPT generates an entry code block specific for each interrupt.
    sub \x23 4, RTOS ; prepare to push 2 values on return stack
    mov IP, 2[RTOS]  ; save IP on return stack
    mov SP, 0[RTOS]  ; save SP pointer on return stack it points to SR on stack
    mov #XXX, IP     ; Move address of thread of interrupt handler in IP
    mov @IP+, PC     ; NEXT
)

( Entering an interrupt handler )
CODE DO-INTERRUPT ( R: - int-sys )
    ." \t ; save registers\n "
    ." \t push R6\n "
    ." \t push R7\n "
    ." \t push R8\n "
    ." \t push R9\n "
    ." \t push R10\n "
    ." \t push R11\n "
    ." \t push R12\n "
    ." \t push R13\n "
    ." \t push R14\n "
    ." \t push R15\n "
    ASM-NEXT
END-CODE

( Restore state at exit of interrupt handler )
CODE EXIT-INTERRUPT ( R: int-sys - )
    ." \t ; restore registers\n "
    ." \t pop R15\n "
    ." \t pop R14\n "
    ." \t pop R13\n "
    ." \t pop R12\n "
    ." \t pop R11\n "
    ." \t pop R10\n "
    ." \t pop R9\n "
    ." \t pop R8\n "
    ." \t pop R7\n "
    ." \t pop R6\n "
    ." \t incd RTOS ; forget about pointer to SR on stack \n "
    ." \t mov @RTOS+, IP  \t; get last position from return stack \n "
    ." \t reti\n "
END-CODE

( Patch the saved status register so that LPM modes are exit after the
  interrupt handler is finished.

  Only allowed in INTERRUPT definition. Not in called functions.
  May be called multiple times.
)
CODE WAKEUP ( R: int-sys - int-sys )
    ." \t mov @RTOS, W        \t; read pointer to SR\n "
    ." \t bic \x23 LPM4, 0(W) \t; patch SR on stack\n "
    ASM-NEXT
END-CODE

