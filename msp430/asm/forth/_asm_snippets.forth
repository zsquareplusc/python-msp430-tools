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

( > Emit the carriage character. )
: CR    13 EMIT ;

( > Emit a blank. )
: SPACE 32 EMIT ;

( > Emit the hash character. )
: HASH  35 EMIT ;

( > Emit the text for a define. )
: DEFINE HASH ." define " SPACE ;

( > Emit assembler for NEXT. )
: ASM-NEXT ." \t br @IP+ \t; NEXT \n " ;

( > Emit assembler for DROP. )
: ASM-DROP ." \t incd SP \t; DROP \n " ;

( > Emit assembler to pop top of stack to register R15. )
: TOS->R15 ." \t pop  R15 \n " ;

( > Emit assembler to pop top of stack to register R14. )
: TOS->R14 ." \t pop  R14 \n " ;

( > Emit assembler to push R15 on stack. )
: R15->TOS ." \t push R15 \n " ;

( > Emit assembler to pop top of stack to register W. )
: TOS->W   ." \t pop  W \n " ;

( > Emit assembler to push register W on stack. )
: W->TOS   ." \t push W \n " ;


