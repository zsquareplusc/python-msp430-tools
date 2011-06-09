( MSP430 specific low level operations

  vi:ft=forth
)

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 8 bit operations )

CODE CRESET ( n adr - )
    TOS->R15
    TOS->R14
    ." \t bic.b R14, 0(R15) " NL
    ASM-NEXT
END-CODE

CODE CSET ( n adr - )
    TOS->R15
    TOS->R14
    ." \t bis.b R14, 0(R15) " NL
    ASM-NEXT
END-CODE

CODE CTOGGLE ( n adr - )
    TOS->R15
    TOS->R14
    ." \t xor.b R14, 0(R15) " NL
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 16 bit operations )

CODE RESET ( n adr - )
    TOS->W
    ." \t bic @SP+, 0(W) " NL
    ASM-NEXT
END-CODE

CODE SET ( n adr - )
    TOS->W
    ." \t bis @SP+, 0(W) " NL
    ASM-NEXT
END-CODE

CODE TOGGLE ( n adr - )
    TOS->W
    ." \t xor @SP+, 0(W) " NL
    ASM-NEXT
END-CODE


( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Miscellaneous functions )

( Simple busy-wait type delay. 3 cycles/loop. )
CODE DELAY ( n - )
    TOS->W
    ." .loop: \t dec W \n "
    ." \t jnz .loop \n "
    ASM-NEXT
END-CODE
