( Some assembler snippets that are commonly used.

  vi:ft=forth
)

: SPACE 32 EMIT ;
: HASH 35 EMIT ;
: NL 10 EMIT ;

: DEFINE HASH ." define " SPACE ;
: NEXT ." \t mov @IP+, PC ; NEXT \n " ;
: TOS->R15 ." \t mov @TOS+, R15 \n " ;
: TOS->R14 ." \t mov @TOS+, R14 \n " ;
: R15->TOS ." \t mov R15, 0(TOS) \n\t decd TOS \n " ;

: DROP-ASM ." \t incd TOS ; DROP " NL ;

