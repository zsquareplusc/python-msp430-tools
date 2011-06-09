( Implementations of builtins.
  These functions are provided for the host in the msp430.asm.forth module. The
  implementations here are for the target.

  vi:ft=forth
)

( ----- low level supporting functions ----- )

CODE LIT
    ." \t push @IP+     ; copy value from thread to stack \n "
    ASM-NEXT
END-CODE

CODE BRANCH
    ." \t add @IP, IP \n "
    ASM-NEXT
END-CODE-INTERNAL

CODE BRANCH0
    ." \t mov @IP+, W ; get offset \n "
    ." \t tst 0(SP)   ; check TOS \n "
    ." \t jnz .Lnjmp  ; skip next if non zero \n "
    ." \t decd IP     ; offset is relative to position of offset, correct \n "
    ." \t add W, IP   ; adjust IP \n "
." .Lnjmp: "
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

( ----- Stack ops ----- )

CODE DROP
    ." \t incd SP " NL
    ASM-NEXT
END-CODE-INTERNAL

CODE DUP
    ." \t push 0(SP) " NL
    ASM-NEXT
END-CODE-INTERNAL

CODE OVER
    ." \t push 2(TOS) " NL
    ASM-NEXT
END-CODE-INTERNAL

( Push a copy of the N'th element )
CODE PICK ( n - n )
    TOS->W                    ( get element number from stack )
    ." \t rla W " NL          ( multiply by 2 -> 2 byte / cell )
    ." \t add SP, W " NL      ( calculate address on stack )
    ." \t push 0(W) " NL
    ASM-NEXT
END-CODE-INTERNAL

CODE SWAP ( y x - x y )
    ." \t mov 2(SP), W " NL
    ." \t mov 0(SP), 2(SP) " NL
    ." \t mov W, 0(SP) " NL
    ASM-NEXT
END-CODE-INTERNAL

( ----- MATH ----- )

CODE +
    ." \t add 0(SP), 2(SP) ; y = x + y " NL
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE -
    ." \t sub 0(SP), 2(SP) ; y = y - x " NL
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

( ----- bit - ops ----- )
CODE AND
    ." \t and 0(SP), 2(SP) ; y = x & y " NL
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE OR
    ." \t bis 0(SP), 2(SP) ; y = x | y " NL
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE XOR
    ." \t xor 0(SP), 2(SP) ; y = x ^ y " NL
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE INVERT
    ." \t inv 0(SP) ; x = ~x " NL
    ASM-NEXT
END-CODE-INTERNAL


( Multiply by two (arithmetic left shift) )
CODE 2* ( n -- n*2 )
    ." \t rla 0(SP) ; x <<= 1 " NL
    ASM-NEXT
END-CODE-INTERNAL

( Divide by two (arithmetic right shift) )
CODE 2/ ( n -- n/2 )
    ." \t rra 0(SP) ; x >>= 1 " NL
    ASM-NEXT
END-CODE-INTERNAL


( Logical left shift by u bits )
CODE LSHIFT ( n u -- n*2^u )
    TOS->W
    ." .lsh:\t clrc " NL
    ." \t rlc 0(SP) ; x <<= 1 " NL
    ." \t dec W " NL
    ." \t jnz .lsh W " NL
    ASM-NEXT
END-CODE-INTERNAL

( Logical right shift by u bits )
CODE RSHIFT ( n -- n/2^-u )
    TOS->W
    ." .rsh:\t clrc " NL
    ." \t rrc 0(SP) ; x >>= 1 " NL
    ." \t dec W " NL
    ." \t jnz .rsh W " NL
    ASM-NEXT
END-CODE-INTERNAL

( ----- Logic ops ----- )
( include normalize to boolean )

CODE NOT
    ." \t tst 0(SP) " NL
    ." \t jnz .not0 " NL
    ." \t mov \x23 -1, 0(SP) " NL       ( replace TOS w/ result )
    ." \t jmp .not2 " NL
    ." .not0: " NL
    ." \t mov \x23 0, 0(SP) " NL       ( replace TOS w/ result )
    ." .not2: " NL
    ASM-NEXT
END-CODE-INTERNAL

( ---------------------------------------------------
    "MIN" """Leave the smaller of two values on the stack"""
    "MAX" """Leave the larger of two values on the stack"""
    "*"
    "/"
)
( ----- Compare ----- )
CODE cmp_set_true   ( n - n )
    ." \t mov \x23 -1, 0(SP) " NL   ( replace argument w/ result )
    ASM-NEXT
END-CODE

CODE cmp_set_false
    ." \t mov \x23 0, 0(SP) " NL   ( replace argument w/ result )
    ASM-NEXT
END-CODE


CODE cmp_true
    ASM-DROP                        ( remove 1nd argument )
    ." \t mov \x23 -1, 0(SP) " NL   ( replace 2nd argument w/ result )
    ASM-NEXT
END-CODE

CODE cmp_false
    ASM-DROP                        ( remove 1nd argument )
    ." \t mov \x23 0, 0(SP) " NL    ( replace 2nd argument w/ result )
    ASM-NEXT
END-CODE


CODE <
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jl  _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE >
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jl  _cmp_false " NL
    ." \t jmp _cmp_true " NL
END-CODE-INTERNAL

CODE <=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jge _cmp_false " NL
    ." \t jmp _cmp_true " NL
END-CODE-INTERNAL

CODE >=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jge _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE ==
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jeq _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

( XXX alias for == )
CODE =
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jeq _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE !=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " NL
    ." \t jne _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL


CODE 0=
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " NL
    ." \t jz  _cmp_set_true " NL
    ." \t jmp _cmp_set_false " NL
END-CODE-INTERNAL

CODE 0>
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " NL
    ." \t jn  _cmp_set_false " NL
    ." \t jmp _cmp_set_true " NL
END-CODE-INTERNAL
