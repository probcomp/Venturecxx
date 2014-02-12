#ifndef SP_H
#define SP_H

#include "types.h"
#include "value.h"
#include <map>

struct SPAux;
struct LSR;
struct LatentDB;
struct PSP;
struct gsl_rng;

struct VentureSPRef : VentureValue
{
  VentureSPRef(Node * makerNode): makerNode(makerNode) {}
  Node * makerNode;
};

struct SPFamilies
{
  SPFamilies() {}
  SPFamilies(const map<FamilyID,RootOfFamily> & families): families(families) {}

  map<FamilyID,RootOfFamily> families;
  bool containsFamily(FamilyID id) const;
  Node * getFamily(FamilyID id);
  void registerFamily(FamilyID id,RootOfFamily root);
  void unregisterFamily(FamilyID id);
};

struct SPAux
{
  virtual shared_ptr<SPAux> copy() const;
};

struct VentureSP : VentureValue
{
  VentureSP(PSP * requestPSP, PSP * outputPSP);
  
  shared_ptr<PSP> requestPSP;
  shared_ptr<PSP> outputPSP;

  virtual shared_ptr<SPAux> constructSPAux() const;
  virtual shared_ptr<LatentDB> constructLatentDB() const;
  virtual void simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const;
  virtual double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  virtual bool hasAEKernel() const;
};




#endif
