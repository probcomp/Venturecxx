  bool SPFamilies::containsFamily(FamilyID id) { throw 500; }
  Node * SPFamilies::getFamily(FamilyID id) { throw 500; }
  void SPFamilies::registerFamily(FamilyID id,RootNodePtr root) { throw 500; }
  void SPFamilies::unregisterFamily(FamilyID id) { throw 500; }


shared_ptr<SPAux> SPAux::copy() { throw 500; }

shared_ptr<SPAux> VentureSP::constructSPAux() { throw 500; }
shared_ptr<LatentDB> VentureSP::constructLatentDB() { throw 500; }
  void VentureSP::simulateLatents(SPAux * spaux,LSR * lsr,bool shouldRestore,LatentDB * latentDB) { throw 500; }
  double VentureSP::detachLatents(SPAux * spaux,LSR * lsr,LatentDB * latentDB) { throw 500; }
  bool VentureSP::hasAEKernel() { throw 500; }

