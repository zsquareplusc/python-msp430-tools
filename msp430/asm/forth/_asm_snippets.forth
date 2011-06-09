( Some assembler snippets that are commonly used.

  vi:ft=forth
)

: SPACE 32 EMIT ;
: HASH 35 EMIT ;
: NL 10 EMIT ;

: DEFINE HASH ." define " SPACE ;

: ASM-NEXT ." \t mov @IP+, PC ; NEXT \n " ;
: ASM-DROP ." \t incd SP ; DROP " NL ;

: TOS->R15 ." \t pop  R15 \n " ;
: TOS->R14 ." \t pop  R14 \n " ;
: R15->TOS ." \t push R15 \n " ;

: TOS->W ." \t pop  W \n " ;
: W->TOS ." \t push W \n " ;


