#ifndef SPAUX_H
#define SPAUX_H

/*
SPAux class will store several things, which Venture can only access through opaque methods.
1. Any data that is part of the SPs value
   that it does not want to keep in its closure.
2. Any ESRs that are simulated.
3. Any tracking of sample counts through incorporate
   and remove.
4. Any additional information mapping tokens to
   some way of reconstructing samples.
*/
   
struct SPAux { virtual ~SPAux() =0; };


#endif
