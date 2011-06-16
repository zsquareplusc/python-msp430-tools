// map macros from TI header files to commands for assembler
#define sfrb(x,x_) x=x_
#define sfrw(x,x_) x=x_
#define sfra(x,x_) x=x_

#define const_sfrb(x,x_) sfrb(x,x_)
#define const_sfrw(x,x_) sfrw(x,x_)
#define const_sfra(x,x_) sfra(x,x_)

