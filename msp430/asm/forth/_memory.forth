( Forth functions to read and write memory.

  vi:ft=forth
)

CODE @B ( adr - n )
    ." \t mov @TOS, R15 " NL
    ." \t mov.b @R15, 0(TOS) " NL
    NEXT
END-CODE

CODE !B ( adr n - )
    TOS->R14
    TOS->R15
    ." \t mov.b R14, 0(R15) " NL
    NEXT
END-CODE

CODE @ ( adr - n )
    ." \t mov @TOS, R15 " NL
    ." \t mov @R15, 0(TOS) " NL
    NEXT
END-CODE

CODE ! ( adr n - )
    TOS->R14
    TOS->R15
    ." \t mov R14, 0(R15) " NL
    NEXT
END-CODE
