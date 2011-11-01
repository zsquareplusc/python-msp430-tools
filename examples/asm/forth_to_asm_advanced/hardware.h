#ifndef HARDWARE_H
#define HARDWARE_H

#include <msp430g2231.h>

// Timer A UART configuration
#define TAUART_RX_INTERRUPT __vector_100
#define TAUART_VECTOR       TIMERA1_VECTOR
//~ #define TAUART_TX_DINT

#define TAUART_BIT_TICKS  416 // ~2400 @ 1e6
//~ #define TAUART_BIT_TICKS  208 // ~480 @ 1e6
//~ #define TAUART_BIT_TICKS  104 // ~9600 @ 1e6

#endif // HARDWARE_H
