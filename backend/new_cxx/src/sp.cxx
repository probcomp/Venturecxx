bool SPFamilies::containsFamily(FamilyID id) const { return families.count(id); }
Node * SPFamilies::getFamily(FamilyID id) const
{
  assert(families.count(id));
  return families[id];
}

void SPFamilies::registerFamily(FamilyID id,RootNodePtr root)
{
  assert(!families.count(id));
  families[id] = root;
}

void SPFamilies::unregisterFamily(FamilyID id)
{
  assert(families.count(id));
  families.erase(id);
}

shared_ptr<SPAux> SPAux::copy() { return new SPAux(); }

shared_ptr<SPAux> VentureSP::constructSPAux() const { return new SPAux(); }
shared_ptr<LatentDB> VentureSP::constructLatentDB() const { return NULL; }

void VentureSP::simulateLatents(SPAux * spaux,LSR * lsr,bool shouldRestore,LatentDB * latentDB) const { throw "no default latent handling"; }
double VentureSP::detachLatents(SPAux * spaux,LSR * lsr,LatentDB * latentDB) const { throw "no default latent handling"; }
bool VentureSP::hasAEKernel() const { return false; }


