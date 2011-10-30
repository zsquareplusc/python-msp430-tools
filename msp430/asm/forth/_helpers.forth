( vi:ft=forth

  Helper function to generate text for the assembler.

  Copyright [C] 2011 Chris Liechti <cliechti@gmx.net>
  All Rights Reserved.
  Simplified BSD License [see LICENSE.txt for full text]
)

( > Generate a simple line for headers )
: LINE ( -- )
    ." ; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n "
;

( > Generate a header in the assembler file )
: HEADER ( str -- )
    ." ;============================================================================\n "
    ." ; " SPACE . LF ( print value from stack )
    ." ;============================================================================\n "
;

