( vi:ft=forth

  MSP430 specific low level operations.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

INCLUDE _interrupts.forth

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 8 bit memory operations )

( > Bit clear operation, 8 bit. )
( > Example: ``BIT0 P1OUT CRESET`` )
CODE CRESET ( n adr -- )
    ASM-TOS->R15
    ASM-TOS->R14
    ." \t bic.b R14, 0(R15) \n "
    ASM-NEXT
END-CODE

( > Bit set operation, 8 bit. )
( > Example: ``BIT0 P1OUT CSET`` )
CODE CSET ( n adr -- )
    ASM-TOS->R15
    ASM-TOS->R14
    ." \t bis.b R14, 0(R15) \n "
    ASM-NEXT
END-CODE

( > Bit toggle operation, 8 bit. )
( > Example: ``BIT0 P1OUT CTOGGLE`` )
CODE CTOGGLE ( n adr -- )
    ASM-TOS->R15
    ASM-TOS->R14
    ." \t xor.b R14, 0(R15) \n "
    ASM-NEXT
END-CODE

( > Bit test operation, 8 bit. )
( > Example: ``BIT0 P1IN CTESTBIT IF 1 THEN 0 ENDIF`` )
CODE CTESTBIT ( mask adr -- bool )
    ASM-TOS->W
    ." \t bit.b @W, 0(SP) \n "
    ." \t jz  .cbit0 \n "
    ." \t mov \x23 -1, 0(SP) \n "       ( replace TOS w/ result )
    ." \t jmp .cbit2 \n "
    ." .cbit0:\n "
    ." \t mov \x23 0, 0(SP) \n "        ( replace TOS w/ result )
    ." .cbit2:\n "
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( 16 bit memory operations )

( > Bit clear operation, 16 bit. )
( > Example: ``CCIE TA0CCTL1 RESET`` )
CODE RESET ( n adr -- )
    ASM-TOS->W
    ." \t bic @SP+, 0(W) \n "
    ASM-NEXT
END-CODE

( > Bit set operation, 16 bit. )
( > Example: ``CCIE TA0CCTL1 SET`` )
CODE SET ( n adr -- )
    ASM-TOS->W
    ." \t bis @SP+, 0(W) \n "
    ASM-NEXT
END-CODE

( > Bit toggle operation, 16 bit. )
( > Example: ``CCIE TA0CCTL1 TOGGLE`` )
CODE TOGGLE ( n adr -- )
    ASM-TOS->W
    ." \t xor @SP+, 0(W) \n "
    ASM-NEXT
END-CODE

( > Bit test operation, 16 bit. )
( > Example: ``CCIFG TA0CCTL1 TESTBIT IF 1 ELSE 0 ENDIF`` )
CODE TESTBIT ( mask adr -- bool )
    ASM-TOS->W
    ." \t bit @W, 0(SP) \n "
    ." \t jz  .bit0 \n "
    ." \t mov \x23 -1, 0(SP) \n "       ( replace TOS w/ result )
    ." \t jmp .bit2 \n "
    ." .bit0:\n"
    ." \t mov \x23 0, 0(SP) \n "        ( replace TOS w/ result )
    ." .bit2:\n"
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( some native implementations that are more compact than the provided Forth words )

( > Increment value on stack by one. )
CODE 1+ ( n -- n )
    ." \t inc 0(SP) \n "
    ASM-NEXT
END-CODE

( > Increment value on stack by two. )
CODE 2+ ( n -- n )
    ." \t incd 0(SP) \n "
    ASM-NEXT
END-CODE

( > Increment value on stack by four. )
CODE 4+ ( n -- n )
    ." \t add \x23 4, 0(SP) \n "
    ASM-NEXT
END-CODE


( > Decrement value on stack by one. )
CODE 1- ( n -- n )
    ." \t dec 0(SP) \n "
    ASM-NEXT
END-CODE

( > Decrement value on stack by two. )
CODE 2- ( n -- n )
    ." \t decd 0(SP) \n "
    ASM-NEXT
END-CODE

( > Decrement value on stack by four. )
CODE 4- ( n -- n )
    ." \t sub \x23 4, 0(SP) \n "
    ASM-NEXT
END-CODE

( > Drop two items from the stack. )
CODE 2DROP ( n n -- )
    ASM-DROP
    ASM-DROP
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( Miscellaneous functions )

( > Simple busy-wait type delay. 3 cycles/loop. )
( > Example: ``20 DELAY`` )
CODE DELAY ( n -- )
    ASM-TOS->W
    ." .loop: \t dec W \n "
    ." \t jnz .loop \n "
    ASM-NEXT
END-CODE

( - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - )
( custom extensions )


( > Swap high/low byte. )
CODE SWPB ( n -- n )
    ." \t swpb 0(SP) \n "
    ASM-NEXT
END-CODE

( > Sign extend an 8 bit value on stack to 16 bits. )
CODE SIGN-EXTEND ( n -- n )
    ." \t sxt 0(SP) \n "
    ASM-NEXT
END-CODE

( > Move byte from memory to memory, 8 bit. )
CODE C@! ( src-adr dst-adr -- )
    ASM-TOS->R15                    ( pop destination address )
    ASM-TOS->R14                    ( pop source address )
    ." \t mov.b @R14, 0(R15) \n "   ( copy value from src to dst )
    ASM-NEXT
END-CODE

( > Move word from memory to memory, 16 bit. )
CODE @! ( src-adr dst-adr -- )
    ASM-TOS->R15                    ( pop destination address )
    ASM-TOS->R14                    ( pop source address )
    ." \t mov @R14, 0(R15) \n "     ( copy value from src to dst )
    ASM-NEXT
END-CODE


( > NOP - waste some small amount of CPU time. )
CODE NOP ( -- )
    ." \t nop\n "
    ASM-NEXT
END-CODE

( > Enable interrupts. )
CODE EINT ( -- )
    ." \t eint\n "
    ASM-NEXT
END-CODE

( > Disable interrupts. )
CODE DINT ( -- )
    ." \t dint\n "
    ASM-NEXT
END-CODE

( > Enter low-power mode LPM0. )
CODE ENTER-LPM0 ( n -- )
    ." \t bis \x23 LPM0, SR\n "
    ASM-NEXT
END-CODE

( > Enter low-power mode LPM1. )
CODE ENTER-LPM1 ( n -- )
    ." \t bis \x23 LPM2, SR\n "
    ASM-NEXT
END-CODE

( > Enter low-power mode LMP2. )
CODE ENTER-LPM2 ( n -- )
    ." \t bis \x23 LPM3, SR\n "
    ASM-NEXT
END-CODE

( > Enter low-power mode LPM3. )
CODE ENTER-LPM3 ( n -- )
    ." \t bis \x23 LPM3, SR\n "
    ASM-NEXT
END-CODE

( > Enter low-power mode LPM4. )
CODE ENTER-LPM4 ( n -- )
    ." \t bis \x23 LPM4, SR\n "
    ASM-NEXT
END-CODE

