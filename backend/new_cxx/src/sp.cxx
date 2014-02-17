#include "sp.h"
#include "node.h"
#include "psp.h"



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

//shared_ptr<SPAux> SPAux::copy() { return new SPAux(); }

shared_ptr<LatentDB> SP::constructLatentDB() const { return shared_ptr<LatentDB>(); }

SP::SP(PSP * requestPSP, PSP * outputPSP) :
  requestPSP(shared_ptr<PSP>(requestPSP)),
  outputPSP(shared_ptr<PSP>(outputPSP))
  {}

void SP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }
double SP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }


shared_ptr<PSP> SP::getPSP(ApplicationNode * node) const
{
  if (dynamic_cast<RequestNode*>(node)) { return requestPSP; }
  else { return outputPSP; }
}


void SP::AEInfer(VentureValuePtr value, shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }

boost::python::dict VentureSPRef::toPython() const 
{ 
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = false;
  return value;
}
