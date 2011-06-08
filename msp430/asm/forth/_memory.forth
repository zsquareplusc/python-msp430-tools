( Forth functions to read and write memory.

  vi:ft=forth
)

CODE C@ ( adr - n )
    ." \t mov @TOS, R15 " NL
    ." \t mov.b @R15, 0(TOS) " NL
    NEXT
END-CODE

CODE C! ( n adr - )
    TOS->R15
    TOS->R14
    ." \t mov.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE @ ( adr - n )
    ." \t mov @TOS, R15 " NL
    ." \t mov @R15, 0(TOS) " NL
    NEXT
END-CODE

CODE ! ( n adr - )
    TOS->R15
    TOS->R14
    ." \t mov R14, 0(R15) " NL
    NEXT
END-CODE
