( Implementations of builtins.
  These functions are provided for the host in the msp430.asm.forth module. The
  implementations here are for the target.

  vi:ft=forth
)

( ----- low level supporting functions ----- )

CODE LIT
    ." \t decd TOS         ; prepare push on stack \n "
    ." \t mov @IP+, 0(TOS) ; copy value from thread to stack \n "
    NEXT
END-CODE

CODE BRANCH
    ." \t add @IP+, IP \n "
    ." \t decd IP \n "
    NEXT
END-CODE-INTERNAL

CODE BRANCH0
    ." \t mov @IP+, W ; get offset \n "
    ." \t tst 0(TOS)  ; check TOS \n "
    ." \t jnz .Lnjmp  ; skip next if non zero \n "
    ." \t decd IP     ; offset is relative to position of offset, correct \n "
    ." \t add W, IP   ; adjust IP \n "
." .Lnjmp: "
    DROP-ASM
    NEXT
END-CODE-INTERNAL

( ----- Stack ops ----- )

CODE DROP
    ." \t incd TOS " NL
    NEXT
END-CODE-INTERNAL

CODE DUP
    ." \t decd TOS " NL
    ." \t mov 2(TOS), 0(TOS) " NL
    NEXT
END-CODE-INTERNAL

CODE OVER
    ." \t decd TOS " NL
    ." \t mov 4(TOS), 0(TOS) " NL
    NEXT
END-CODE-INTERNAL

( Push a copy of the N'th element )
CODE PICK ( n - n )
    TOS->R15                    ( get element number from stack )
    ." \t rla R15 " NL          ( multiply by 2 -> 2 byte / cells )
    ." \t add TOS, R15 " NL     ( calculate address on stack )
    ." \t decd TOS " NL         ( push copy )
    ." \t mov 0(R15), 0(TOS) " NL
    NEXT
END-CODE-INTERNAL

CODE SWAP ( y x - x y )
    ." \t mov 2(TOS), W " NL
    ." \t mov 0(TOS), 2(TOS) " NL
    ." \t mov W, 0(TOS) " NL
    NEXT
END-CODE-INTERNAL

( ----- MATH ----- )

CODE +
    ." \t add 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

CODE -
    ." \t sub 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

( ----- bit - ops ----- )
CODE &
    ." \t and 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

CODE |
    ." \t bis 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

CODE ^
    ." \t xor 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

CODE ~
    ." \t inv 0(TOS), 2(TOS) " NL
    DROP-ASM
    NEXT
END-CODE-INTERNAL

( ----- Logic ops ----- )
( include normalize to boolean )

CODE NOT
    ." \t tst 0(TOS) " NL
    ." \t jnz .not0 " NL
    ." \t mov \x23 -1, 0(TOS) " NL       ( replace TOS w/ result )
    ." \t jmp .not2 " NL
    ." .not0: " NL
    ." \t mov \x23 0, 0(TOS) " NL       ( replace TOS w/ result )
    ." .not2: " NL
    NEXT
END-CODE-INTERNAL

( ---------------------------------------------------
    "MIN" """Leave the smaller of two values on the stack"""
    "MAX" """Leave the larger of two values on the stack"""
    "*"
    "/"
    "NEG"
    "<<"
    ">>"
    "NOT"
    "AND"
    "OR"
)
( ----- Compare ----- )
CODE cmp_set_true   ( n - n )
    ." \t mov \x23 -1, 0(TOS) " NL   ( replace argument w/ result )
    NEXT
END-CODE

CODE cmp_set_false
    ." \t mov \x23 0, 0(TOS) " NL   ( replace argument w/ result )
    NEXT
END-CODE


CODE cmp_true
    DROP-ASM                        ( remove 1nd argument )
    ." \t mov \x23 -1, 0(TOS) " NL   ( replace 2nd argument w/ result )
    NEXT
END-CODE

CODE cmp_false
    DROP-ASM                        ( remove 1nd argument )
    ." \t mov \x23 0, 0(TOS) " NL   ( replace 2nd argument w/ result )
    NEXT
END-CODE


CODE <
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jl  _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE >
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jl  _cmp_false " NL
    ." \t jmp _cmp_true " NL
END-CODE-INTERNAL

CODE <=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jge _cmp_false " NL
    ." \t jmp _cmp_true " NL
END-CODE-INTERNAL

CODE >=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jge _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE ==
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jeq _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

( XXX alias for == )
CODE ==
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jeq _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL

CODE !=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(TOS), 2(TOS) " NL
    ." \t jne _cmp_true " NL
    ." \t jmp _cmp_false " NL
END-CODE-INTERNAL


CODE 0=
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(TOS) " NL
    ." \t jz  _cmp_set_true " NL
    ." \t jmp _cmp_set_false " NL
END-CODE-INTERNAL

CODE 0>
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(TOS) " NL
    ." \t jn  _cmp_set_false " NL
    ." \t jmp _cmp_set_true " NL
END-CODE-INTERNAL
