( vi:ft=forth

  Some assembler snippets that are commonly used.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

( > Emit the backspace character. )
: BS     8 EMIT ;

( > Emit the line feed character. )
: LF    10 EMIT ;

( > Emit the hash character. )
: HASH  35 EMIT ;

( > Emit the text for a define. )
: DEFINE HASH ." define " SPACE ;

( > Emit assembler for NEXT. )
: ASM-NEXT ." \t br @IP+ \t; NEXT \n " ;

( > Emit assembler for DROP. )
( > Example::
( >
( >    CODE DROP-DEMO ( n -- )
( >        ASM-DROP
( >        ASM-NEXT
( >    END-CODE )
: ASM-DROP ." \t incd SP \t; DROP \n " ;

( > Emit assembler to pop top of stack to register R15. )
: ASM-TOS->R15 ." \t pop  R15 \n " ;

( > Emit assembler to pop top of stack to register R14. )
: ASM-TOS->R14 ." \t pop  R14 \n " ;

( > Emit assembler to push R15 on stack. )
: ASM-R15->TOS ." \t push R15 \n " ;

( > Emit assembler to pop top of stack to register W. )
: ASM-TOS->W   ." \t pop  W \n " ;

( > Emit assembler to push register W on stack. )
: ASM-W->TOS   ." \t push W \n " ;

( > Helper to write a call in assembler. )
( > Example::
( >
( >    CODE PUTCHAR ( u -- )
( >        ASM-TOS->R15
( >        ASM-CALL putchar
( >        ASM-NEXT
( >    END-CODE )
( The function inserts commands in the currently compiling frame so that the
  corresponding assembler snippet is output when that functionis called. ASM-CALL
  itself is immediate [executed during compilation].)
: ASM-CALL
    ' LIT , " \t call \x23" , ' . ,     ( output string )
    ' LIT , WORD , ' . ,                ( output saved word )
    ' LF ,                              ( output newline )
IMMEDIATE ;
