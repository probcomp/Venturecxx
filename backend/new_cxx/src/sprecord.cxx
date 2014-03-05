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

boost::python::dict VentureSPRecord::toPython(ConcreteTrace * trace) const
{
  boost::python::dict value;
  value["type"] = "spRecord";
  value["value"] = boost::python::object("spRecord");
  return value;
}

string VentureSPRecord::toString() const { return "spRecord"; }
