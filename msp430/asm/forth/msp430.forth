( MSP430 specific low level operations

  vi:ft=forth
)

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 8 bit operations )

CODE CRESET ( n adr - )
    TOS->R15
    TOS->R14
    ." \t bic.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE CSET ( n adr - )
    TOS->R15
    TOS->R14
    ." \t bis.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE CTOGGLE ( n adr - )
    TOS->R15
    TOS->R14
    ." \t xor.b R14, 0(R15) " NL
    NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 16 bit operations )

CODE RESET ( n adr - )
    TOS->R15
    ." \t bic @TOS+, 0(R15) " NL
    NEXT
END-CODE

CODE SET ( n adr - )
    TOS->R15
    ." \t bis @TOS+, 0(R15) " NL
    NEXT
END-CODE

CODE TOGGLE ( n adr - )
    TOS->R15
    ." \t xor @TOS+, 0(R15) " NL
    NEXT
END-CODE


( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Miscellaneous functions )

( Simple busy-wait type delay. 3 cycles/loop. )
CODE DELAY ( n - )
    TOS->R15
    ." .loop: \t dec R15 \n "
    ." \t jnz .loop \n "
    NEXT
END-CODE
