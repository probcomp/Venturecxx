#ifndef SP_RECORD_H
#define SP_RECORD_H

#include "types.h"
#include "sp.h"

struct ConcreteTrace;

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

  int getValueTypeRank() const;
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython(ConcreteTrace * trace) const;
  string toString() const;

  VentureSPRecord* copy_help(ForwardingMap* m) const;
};


#endif
