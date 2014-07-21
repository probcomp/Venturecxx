#include "sprecord.h"

// TODO hacky
bool VentureSPRecord::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureSPRecord> other_v = dynamic_pointer_cast<VentureSPRecord>(other);
  return other_v && (other_v->sp.get() == sp.get());
}

size_t VentureSPRecord::hash() const 
{ 
  boost::hash<long> long_hash;
  return long_hash(reinterpret_cast<long>(sp.get()));
}

boost::python::dict VentureSPRecord::toPython(Trace * trace) const
{
  return sp->toPython(trace, spAux);
}

string VentureSPRecord::toString() const { return "spRecord"; }
