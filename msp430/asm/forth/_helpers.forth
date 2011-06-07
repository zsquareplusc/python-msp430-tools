( Helper function to generate text for the assembler.

  vi:ft=forth
)

( Generate a simple line for headers )
: LINE ( - )
    ." ; - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - " NL
;

( Generate a header in the assembler file )
: HEADER ( s - )
    ." ;============================================================================ " NL
    ." ; " SPACE . NL ( print value from stack )
    ." ;============================================================================ " NL
;

