#ifndef SPAUX_H
#define SPAUX_H

#include <map>

using namespace std;

struct Node;

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
   

/* evalFamily, restoreFamily, detachFamily */

/* spAux more than before, used for exposed simulation requests */
struct SPAux 
{
  /* TODO Exposed simulation requests, Latent simulation requests */
  /* Want this to be unordered_map, but problem with hashing. */

  map<size_t,Node*> families;

  /* The vector is a collection of VentureValues that this family
     "owns", e.g. values cloned during msp.simulateRequest(val) */
  map<size_t,vector<VentureValue*> > familyValues;

  virtual ~SPAux() {}; 
};


#endif
