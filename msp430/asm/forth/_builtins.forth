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
END-CODE

CODE BRANCH0
    ." \t mov @IP+, W \t; get offset \n "
    ." \t tst 0(SP)   \t; check TOS \n "
    ." \t jnz .Lnjmp  \t; skip next if non zero \n "
    ." \t decd IP     \t; offset is relative to position of offset, correct \n "
    ." \t add W, IP   \t; adjust IP \n "
." .Lnjmp: "
    ASM-DROP
    ASM-NEXT
END-CODE

( ----- Stack ops ----- )

CODE DROP
    ." \t incd SP\n "
    ASM-NEXT
END-CODE

CODE DUP
(    ." \t push @SP\n " )
    ." \t mov @SP, W\n "
    ." \t push W\n "
    ASM-NEXT
END-CODE

CODE OVER
(    ." \t push 2(TOS\n " )
    ." \t mov 2(SP), W\n "
    ." \t push W\n "
    ASM-NEXT
END-CODE

( Push a copy of the N'th element )
CODE PICK ( n - n )
    TOS->W                    ( get element number from stack )
    ." \t rla W " LF          ( multiply by 2 -> 2 byte / cell )
    ." \t add SP, W " LF      ( calculate address on stack )
    ." \t push 0(W) " LF
    ASM-NEXT
END-CODE

CODE SWAP ( y x - x y )
    ." \t mov 2(SP), W " LF
    ." \t mov 0(SP), 2(SP) " LF
    ." \t mov W, 0(SP) " LF
    ASM-NEXT
END-CODE

( ----- Return Stack ops ----- )

( Move x to the return stack. )
CODE >R ( x -- ) ( R: -- x )
    ." \t decd RTOS \t; make room on the return stack\n "
    ." \t pop 0(RTOS) \t; pop value and put it on return stack\n "
    ASM-NEXT
END-CODE

( Move x from the return stack to the data stack. )
CODE R> ( -- x ) ( R: x -- )
    ." \t push @RTOS+ \t; pop from return stack, push to data stack\n "
    ASM-NEXT
END-CODE

( Copy x from the return stack to the data stack. )
CODE R@ ( -- x ) ( R: x -- x )
    ." \t push @RTOS \t; push copy of RTOS to data stack\n "
    ASM-NEXT
END-CODE


( ----- MATH ----- )

CODE +
    ." \t add 0(SP), 2(SP) \t; y = x + y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

CODE -
    ." \t sub 0(SP), 2(SP) \t; y = y - x " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( ----- bit - ops ----- )
CODE AND
    ." \t and 0(SP), 2(SP) \t; y = x & y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

CODE OR
    ." \t bis 0(SP), 2(SP) \t; y = x | y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

CODE XOR
    ." \t xor 0(SP), 2(SP) \t; y = x ^ y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

CODE INVERT
    ." \t inv 0(SP) \t; x = ~x " LF
    ASM-NEXT
END-CODE


( Multiply by two (arithmetic left shift) )
CODE 2* ( n -- n*2 )
    ." \t rla 0(SP) \t; x <<= 1 " LF
    ASM-NEXT
END-CODE

( Divide by two (arithmetic right shift) )
CODE 2/ ( n -- n/2 )
    ." \t rra 0(SP) \t; x >>= 1 " LF
    ASM-NEXT
END-CODE


( Logical left shift by u bits )
CODE LSHIFT ( n u -- n*2^u )
    TOS->W
    ." .lsh:\t clrc " LF
    ." \t rlc 0(SP) \t; x <<= 1 " LF
    ." \t dec W " LF
    ." \t jnz .lsh W " LF
    ASM-NEXT
END-CODE

( Logical right shift by u bits )
CODE RSHIFT ( n -- n/2^-u )
    TOS->W
    ." .rsh:\t clrc " LF
    ." \t rrc 0(SP) \t; x >>= 1 " LF
    ." \t dec W " LF
    ." \t jnz .rsh W " LF
    ASM-NEXT
END-CODE

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
END-CODE

( ---------------------------------------------------
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
END-CODE

CODE >
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 2(SP), 0(SP) " LF
    ." \t jl  _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE

CODE <=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge _cmp_false " LF
    ." \t jmp _cmp_true " LF
END-CODE

CODE >=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE

CODE ==
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE

( XXX alias for == )
CODE =
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE

CODE !=
    DEPENDS-ON cmp_true
    DEPENDS-ON cmp_false
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jne _cmp_true " LF
    ." \t jmp _cmp_false " LF
END-CODE


CODE 0=
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " LF
    ." \t jz  _cmp_set_true " LF
    ." \t jmp _cmp_set_false " LF
END-CODE

CODE 0>
    DEPENDS-ON cmp_set_true
    DEPENDS-ON cmp_set_false
    ." \t tst 0(SP) " LF
    ." \t jn  _cmp_set_false " LF
    ." \t jmp _cmp_set_true " LF
END-CODE

( --------------------------------------------------- )

( XXX Forth name ERASE conflicts with FCTL bit name in MSP430 )
( Erase memory area )
CODE ZERO ( adr u - )
    TOS->W      ( count )
    TOS->R15    ( address )
    ." .erase_loop: clr.b 0(R15)\n"
    ." \t inc R15\n"
    ." \t dec W\n"
    ." \t jnz .erase_loop\n"
    ASM-NEXT
END-CODE

( --------------------------------------------------- )
( helper for ." )
CODE __write_text
    ." \t mov @IP+, R15\n"
    ." \t call \x23 write\n"
    ASM-NEXT
END-CODE

