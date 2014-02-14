#include "sp.h"
#include "node.h"
#include "psp.h"

bool SPFamilies::containsFamily(FamilyID id)  { return families.count(id); }
RootOfFamily SPFamilies::getFamily(FamilyID id) 
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

shared_ptr<SPAux> VentureSP::constructSPAux() const { return shared_ptr<SPAux>(new SPAux()); }
shared_ptr<LatentDB> VentureSP::constructLatentDB() const { return shared_ptr<LatentDB>(); }

VentureSP::VentureSP(PSP * requestPSP, PSP * outputPSP) :
  requestPSP(shared_ptr<PSP>(requestPSP)),
  outputPSP(shared_ptr<PSP>(outputPSP))
  {}

void VentureSP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }
double VentureSP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }
bool VentureSP::hasAEKernel() const { return false; }


shared_ptr<PSP> VentureSP::getPSP(ApplicationNode * node) const
{
  if (dynamic_cast<RequestNode*>(node)) { return requestPSP; }
  else { return outputPSP; }
}

boost::python::dict VentureSPRef::toPython() const 
{ 
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = false;
  return value;
}
