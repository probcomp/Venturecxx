#include "sp.h"
#include "node.h"
#include "psp.h"
#include "concrete_trace.h"
#include "stop-and-copy.h"

bool SPFamilies::containsFamily(FamilyID id)  { return families.count(id); }
RootOfFamily SPFamilies::getRootOfFamily(FamilyID id) 
{
  assert(families.count(id));
  return families[id];
}

void SPFamilies::registerFamily(FamilyID id,RootOfFamily root)
{
  assert(!families.count(id));
  families[id] = root;
}

void SPFamilies::unregisterFamily(FamilyID id)
{
  assert(families.count(id));
  families.erase(id);
}

shared_ptr<SPAux> SPAux::clone()
{
  ForwardingMap m = ForwardingMap();
  return shared_ptr<SPAux>(this->copy_help(&m));
}

shared_ptr<LatentDB> SP::constructLatentDB() const { return shared_ptr<LatentDB>(); }

SP::SP(PSP * requestPSP, PSP * outputPSP) :
  requestPSP(shared_ptr<PSP>(requestPSP)),
  outputPSP(shared_ptr<PSP>(outputPSP))
  {}

double SP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const { assert(false); throw "no default latent handling"; }
double SP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }


shared_ptr<PSP> SP::getPSP(ApplicationNode * node) const
{
  if (dynamic_cast<RequestNode*>(node)) { return requestPSP; }
  else { return outputPSP; }
}

void SP::AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }

boost::python::object SPAux::toPython(Trace * trace) const
{
  return boost::python::object("unknown spAux");
}

boost::python::dict SP::toPython(Trace * trace, shared_ptr<SPAux> spAux) const
{
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = "unknown";
  return value;
}

boost::python::dict VentureSPRef::toPython(Trace * trace) const 
{
  return trace->getMadeSP(makerNode)->toPython(trace, trace->getMadeSPAux(makerNode));
}

bool VentureSPRef::equals(const VentureValuePtr & other) const
{
  shared_ptr<VentureSPRef> other_v = dynamic_pointer_cast<VentureSPRef>(other);
  return other_v && (other_v->makerNode == makerNode);
}

size_t VentureSPRef::hash() const 
{ 
  boost::hash<long> long_hash;
  return long_hash(reinterpret_cast<long>(makerNode));
}

string VentureSPRef::toString() const { return "spRef"; }
