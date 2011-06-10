( Implementations of builtins.
  These functions are provided for the host in the msp430.asm.forth module. The
  implementations here are for the target.

  vi:ft=forth
)

( ----- low level supporting functions ----- )

CODE LIT
    ." \t push @IP+   \t; copy value from thread to stack \n "
    ASM-NEXT
END-CODE

CODE BRANCH
    ." \t add @IP, IP \n "
    ASM-NEXT
END-CODE-INTERNAL

CODE BRANCH0
    ." \t mov @IP+, W \t; get offset \n "
    ." \t tst 0(SP)   \t; check TOS \n "
    ." \t jnz .Lnjmp  \t; skip next if non zero \n "
    ." \t decd IP     \t; offset is relative to position of offset, correct \n "
    ." \t add W, IP   \t; adjust IP \n "
." .Lnjmp: "
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

( ----- Stack ops ----- )

CODE DROP
    ." \t incd SP " LF
    ASM-NEXT
END-CODE-INTERNAL

CODE DUP
    ." \t push 0(SP) " LF
    ASM-NEXT
END-CODE-INTERNAL

CODE OVER
    ." \t push 2(TOS) " LF
    ASM-NEXT
END-CODE-INTERNAL

( Push a copy of the N'th element )
CODE PICK ( n - n )
    TOS->W                    ( get element number from stack )
    ." \t rla W " LF          ( multiply by 2 -> 2 byte / cell )
    ." \t add SP, W " LF      ( calculate address on stack )
    ." \t push 0(W) " LF
    ASM-NEXT
END-CODE-INTERNAL

CODE SWAP ( y x - x y )
    ." \t mov 2(SP), W " LF
    ." \t mov 0(SP), 2(SP) " LF
    ." \t mov W, 0(SP) " LF
    ASM-NEXT
END-CODE-INTERNAL

( ----- MATH ----- )

CODE +
    ." \t add 0(SP), 2(SP) \t; y = x + y " LF
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE -
    ." \t sub 0(SP), 2(SP) \t; y = y - x " LF
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

( ----- bit - ops ----- )
CODE AND
    ." \t and 0(SP), 2(SP) \t; y = x & y " LF
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE OR
    ." \t bis 0(SP), 2(SP) \t; y = x | y " LF
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE XOR
    ." \t xor 0(SP), 2(SP) \t; y = x ^ y " LF
    ASM-DROP
    ASM-NEXT
END-CODE-INTERNAL

CODE INVERT
    ." \t inv 0(SP) \t; x = ~x " LF
    ASM-NEXT
END-CODE-INTERNAL


( Multiply by two (arithmetic left shift) )
CODE 2* ( n -- n*2 )
    ." \t rla 0(SP) \t; x <<= 1 " LF
    ASM-NEXT
END-CODE-INTERNAL

( Divide by two (arithmetic right shift) )
CODE 2/ ( n -- n/2 )
    ." \t rra 0(SP) \t; x >>= 1 " LF
    ASM-NEXT
END-CODE-INTERNAL


( Logical left shift by u bits )
CODE LSHIFT ( n u -- n*2^u )
    TOS->W
    ." .lsh:\t clrc " LF
    ." \t rlc 0(SP) \t; x <<= 1 " LF
    ." \t dec W " LF
    ." \t jnz .lsh W " LF
    ASM-NEXT
END-CODE-INTERNAL

( Logical right shift by u bits )
CODE RSHIFT ( n -- n/2^-u )
    TOS->W
    ." .rsh:\t clrc " LF
    ." \t rrc 0(SP) \t; x >>= 1 " LF
    ." \t dec W " LF
    ." \t jnz .rsh W " LF
    ASM-NEXT
END-CODE-INTERNAL

( ----- Logic ops ----- )
( include normalize to boolean )

CODE NOT
    ." \t tst 0(SP) " LF
    ." \t jnz .not0 " LF
    ." \t mov \x23 -1, 0(SP) " LF       ( replace TOS w/ result )
    ." \t jmp .not2 " LF
    ." .not0: " LF
    ." \t mov \x23 0, 0(SP) " LF       ( replace TOS w/ result )
    ." .not2: " LF
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
    ." \t mov \x23 -1, 0(SP) " LF   ( replace argument w/ result )
    ASM-NEXT
END-CODE

CODE cmp_set_false
    ." \t mov \x23 0, 0(SP) " LF   ( replace argument w/ result )
    ASM-NEXT
END-CODE


CODE cmp_true
    ASM-DROP                        ( remove 1nd argument )
    ." \t mov \x23 -1, 0(SP) " LF   ( replace 2nd argument w/ result )
    ASM-NEXT
END-CODE

CODE cmp_false
    ASM-DROP                        ( remove 1nd argument )
    ." \t mov \x23 0, 0(SP) " LF    ( replace 2nd argument w/ result )
    ASM-NEXT
END-CODE


CODE <
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jl  _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE-INTERNAL

CODE >
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jl  _cmp_false " LF
    ." \t jmp _cmp_true " LF
END-CODE-INTERNAL

CODE <=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge _cmp_false " LF
    ." \t jmp _cmp_true " LF
END-CODE-INTERNAL

CODE >=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE-INTERNAL

CODE ==
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE-INTERNAL

( XXX alias for == )
CODE =
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE-INTERNAL

CODE !=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jne _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE-INTERNAL


CODE 0=
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " LF
    ." \t jz  _cmp_set_true " LF
    ." \t jmp _cmp_set_false " LF
END-CODE-INTERNAL

CODE 0>
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " LF
    ." \t jn  _cmp_set_false " LF
    ." \t jmp _cmp_set_true " LF
END-CODE-INTERNAL
