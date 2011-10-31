( vi:ft=forth

  Forth functions to read and write memory.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

( > Fetch byte value. )
CODE C@ ( adr -- n )
    ." \t mov @SP, W \n "           ( copy address )
    ." \t mov.b @W, W \n "          ( execute read )
    ." \t mov W, 0(SP) \n "         ( replace TOS with value )
    ASM-NEXT
END-CODE

( > Store byte value. )
CODE C! ( n adr -- )
    ASM-TOS->R15                    ( pop address )
    ASM-TOS->R14                    ( pop value )
    ." \t mov.b R14, 0(R15) \n "    ( write to address - separate instruction b/c byte mode )
    ASM-NEXT
END-CODE

( > Fetch word value. )
CODE @ ( adr -- n )
    ." \t mov @SP, W \n "           ( copy address )
    ." \t mov @W, 0(SP) \n "        ( replace TOS with value )
    ASM-NEXT
END-CODE

( > Store word value. )
CODE ! ( n adr -- )
    ASM-TOS->W                      ( pop address )
    ." \t mov @SP+, 0(W) \n "       ( pop value and write to address )
    ASM-NEXT
END-CODE

