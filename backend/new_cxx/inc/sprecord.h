#ifndef SP_RECORD_H
#define SP_RECORD_H

#include "types.h"

struct SP;
struct SPAux;
struct SPFamilies;

// TODO URGENT not sure when or how this is called yet.
struct VentureSPRecord : VentureValue
{
  VentureSPRecord(SP * sp): sp(sp) {}
  VentureSPRecord(SP * sp,SPAux * spAux): sp(sp), spAux(spAux) {}

  shared_ptr<VentureSP> sp;
  shared_ptr<SPAux> spAux;
  shared_ptr<SPFamilies> spFamilies;


};


#endif
