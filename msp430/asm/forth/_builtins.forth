( vi:ft=forth

  Implementations of some builtins.

  These functions are provided for the host in the msp430.asm.forth module. The
  implementations here are for the target.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

( ----- low level supporting functions ----- )

( > Put a literal [next element within thread] on the stack. )
CODE LIT
    ." \t push @IP+   \t; copy value from thread to stack \n "
    ASM-NEXT
END-CODE

( > Relative jump within a thread. )
CODE BRANCH
    ." \t add @IP, IP \n "
    ASM-NEXT
END-CODE

( > Realtive jump within a thread. But only jump if value on stack is false. )
CODE BRANCH0
    ." \t mov @IP+, W \t; get offset \n "
    ." \t tst 0(SP)   \t; check TOS \n "
    ." \t jnz .Lnjmp  \t; do not adjust IP if non zero \n "
    ." \t decd IP     \t; offset is relative to position of offset, correct \n "
    ." \t add W, IP   \t; adjust IP \n "
." .Lnjmp: "
    ASM-DROP
    ASM-NEXT
END-CODE

( ----- Stack ops ----- )

( > Remove value from top of stack. )
CODE DROP ( x -- )
    ." \t incd SP\n "
    ASM-NEXT
END-CODE

( > Duplicate value on top of stack. )
CODE DUP ( x -- x x )
(    ." \t push @SP\n " )
    ." \t mov @SP, W\n "
    ." \t push W\n "
    ASM-NEXT
END-CODE

( > Push a copy of the second element on the stack. )
CODE OVER ( y x -- y x y )
(    ." \t push 2(TOS\n " )
    ." \t mov 2(SP), W\n "
    ." \t push W\n "
    ASM-NEXT
END-CODE

( > Push a copy of the N'th element. )
CODE PICK ( n -- n )
    ASM-TOS->W                ( get element number from stack )
    ." \t rla W " LF          ( multiply by 2 -> 2 byte / cell )
    ." \t add SP, W " LF      ( calculate address on stack )
    ." \t push 0(W) " LF
    ASM-NEXT
END-CODE

( > Exchange the two topmost values on the stack. )
CODE SWAP ( y x -- x y )
    ." \t mov 2(SP), W " LF
    ." \t mov 0(SP), 2(SP) " LF
    ." \t mov W, 0(SP) " LF
    ASM-NEXT
END-CODE

( ----- Return Stack ops ----- )

( > Move x to the return stack. )
CODE >R ( x -- ) ( R: -- x )
    ." \t decd RTOS \t; make room on the return stack\n "
    ." \t pop 0(RTOS) \t; pop value and put it on return stack\n "
    ASM-NEXT
END-CODE

( > Move x from the return stack to the data stack. )
CODE R> ( -- x ) ( R: x -- )
    ." \t push @RTOS+ \t; pop from return stack, push to data stack\n "
    ASM-NEXT
END-CODE

( > Copy x from the return stack to the data stack. )
CODE R@ ( -- x ) ( R: x -- x )
    ." \t push @RTOS \t; push copy of RTOS to data stack\n "
    ASM-NEXT
END-CODE


( ----- MATH ----- )

( > Add two 16 bit values. )
CODE + ( n n -- n )
    ." \t add 0(SP), 2(SP) \t; y = x + y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( > Subtract two 16 bit values. )
CODE - ( n n -- n )
    ." \t sub 0(SP), 2(SP) \t; y = y - x " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( ----- bit - ops ----- )
( > Bitwise AND. )
CODE AND ( n n -- n )
    ." \t and 0(SP), 2(SP) \t; y = x & y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( > Bitwise OR. )
CODE OR ( n n -- n )
    ." \t bis 0(SP), 2(SP) \t; y = x | y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( > Bitwise XOR. )
CODE XOR ( n n -- n )
    ." \t xor 0(SP), 2(SP) \t; y = x ^ y " LF
    ASM-DROP
    ASM-NEXT
END-CODE

( > Bitwise invert. )
CODE INVERT ( n -- n )
    ." \t inv 0(SP) \t; x = ~x " LF
    ASM-NEXT
END-CODE


( > Multiply by two [arithmetic left shift]. )
CODE 2* ( n -- n*2 )
    ." \t rla 0(SP) \t; x <<= 1 " LF
    ASM-NEXT
END-CODE

( > Divide by two [arithmetic right shift]. )
CODE 2/ ( n -- n/2 )
    ." \t rra 0(SP) \t; x >>= 1 " LF
    ASM-NEXT
END-CODE


( > Logical left shift by u bits. )
CODE LSHIFT ( n u -- n*2^u )
    ASM-TOS->W
    ." .lsh:\t clrc\n"
    ." \t rlc 0(SP) \t; x <<= 1\n"
    ." \t dec W\n"
    ." \t jnz .lsh\n"
    ASM-NEXT
END-CODE

( > Logical right shift by u bits. )
CODE RSHIFT ( n u -- n/2^u )
    ASM-TOS->W
    ." .rsh:\t clrc\n"
    ." \t rrc 0(SP) \t; x >>= 1\n"
    ." \t dec W\n"
    ." \t jnz .rsh\n"
    ASM-NEXT
END-CODE

( ----- Logic ops ----- )
(  0 - false
  -1 - true
)
( > Boolean invert. )
CODE NOT ( b -- b )  ( XXX alias 0= )
    DEPENDS-ON __COMPARE_HELPER
    ." \t tst 0(SP) " LF
    ." \t jz  __set_true " LF
    ." \t jmp __set_false " LF
END-CODE

( ---------------------------------------------------
    "*"
    "/"
)
( ----- Compare ----- )
( > Internal helper. Providing several labels to be called from assembler:
( >
( > - ``__set_true``    stack: ``x -- true`` )
( > - ``__set_false``   stack: ``x -- false`` )
( > - ``__drop_and_set_true``  stack: ``x y -- true`` )
( > - ``__drop_and_set_false`` stack: ``x y -- false`` )
CODE __COMPARE_HELPER
    ." __drop_and_set_true:" LF
    ASM-DROP                        ( remove 1st argument )
    ." __set_true:" LF
    ." \t mov \x23 -1, 0(SP) " LF    ( replace 2nd argument w/ result )
    ASM-NEXT

    ." __drop_and_set_false:" LF
    ASM-DROP                        ( remove 1st argument )
    ." __set_false:" LF
    ." \t mov \x23 0, 0(SP) " LF    ( replace 2nd argument w/ result )
    ASM-NEXT
END-CODE


( > Compare two numbers. )
CODE < ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jl  __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE

( > Compare two numbers. )
CODE > ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 2(SP), 0(SP) " LF
    ." \t jl  __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE

( > Compare two numbers. )
CODE <= ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge __drop_and_set_false " LF
    ." \t jmp __drop_and_set_true " LF
END-CODE

( > Compare two numbers. )
CODE >= ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jge __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE

( > Tests two numbers for equality. )
CODE == ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE

( XXX alias for == )
( > Tests two numbers for equality. )
CODE = ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jeq __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE

( > Tests two numbers for unequality. )
CODE != ( x y -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t cmp 0(SP), 2(SP) " LF
    ." \t jne __drop_and_set_true " LF
    ." \t jmp __drop_and_set_false " LF
END-CODE


( > Test if number equals zero. )
CODE 0= ( x -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t tst 0(SP) " LF
    ." \t jz  __set_true " LF
    ." \t jmp __set_false " LF
END-CODE

( > Test if number is positive. )
CODE 0> ( x -- b )
    DEPENDS-ON __COMPARE_HELPER
    ." \t tst 0(SP) " LF
    ." \t jn  __set_false " LF
    ." \t jmp __set_true " LF
END-CODE

( --------------------------------------------------- )

( XXX Forth name ERASE conflicts with FCTL bit name in MSP430 )
( > Erase memory area. )
CODE ZERO ( adr u -- )
    ASM-TOS->W      ( count )
    ASM-TOS->R15    ( address )
    ." .erase_loop: clr.b 0(R15)\n"
    ." \t inc R15\n"
    ." \t dec W\n"
    ." \t jnz .erase_loop\n"
    ASM-NEXT
END-CODE

( --------------------------------------------------- )
( > internal helper for ``."`` )
CODE __write_text ( -- )
    ." \t mov @IP+, R15\n"
    ." \t call \x23 write\n"
    ASM-NEXT
END-CODE

