#ifndef SP_RECORD_H
#define SP_RECORD_H

#include "types.h"
#include "sp.h"


// TODO URGENT not sure when or how this is called yet.
struct VentureSPRecord : VentureValue
{
  VentureSPRecord(SP * sp): sp(sp), spFamilies(new SPFamilies()) {}
  VentureSPRecord(shared_ptr<SP> sp): sp(sp), spFamilies(new SPFamilies()) {}
  VentureSPRecord(SP * sp,SPAux * spAux): sp(sp), spAux(spAux), spFamilies(new SPFamilies()) {}
  VentureSPRecord(shared_ptr<SP> sp,shared_ptr<SPAux> spAux): sp(sp), spAux(spAux), spFamilies(new SPFamilies()) {}

  shared_ptr<SP> sp;
  shared_ptr<SPAux> spAux;
  shared_ptr<SPFamilies> spFamilies;

  shared_ptr<SPAux> getSPAux() const { return spAux; }
};


#endif
