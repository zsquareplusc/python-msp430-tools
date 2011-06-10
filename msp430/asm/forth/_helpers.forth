( Helper function to generate text for the assembler.

  vi:ft=forth
)

( Generate a simple line for headers )
: LINE ( - )
    ." ; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n "
;

( Generate a header in the assembler file )
: HEADER ( str - )
    ." ;============================================================================\n "
    ." ; " SPACE . LF ( print value from stack )
    ." ;============================================================================\n "
;

