#ifndef SP_H
#define SP_H

#include "types.h"
#include "value.h"
#include <map>

struct SPAux;
struct LSR;
struct LatentDB;

using std::map;

struct VentureSPRef : VentureValue
{
  VentureSPRef(Node * makerNode): makerNode(makerNode) {}
  Node * makerNode;
};

struct SPFamilies
{
  SPFamilies() {}
  SPFamilies(const map<FamilyID,RootNodePtr> & families): families(families) {}

  map<FamilyID,RootNodePtr> families;
  bool containsFamily(FamilyID id) const;
  Node * getFamily(FamilyID id);
  void registerFamily(FamilyID id,RootNodePtr root);
  void unregisterFamily(FamilyID id);
};

struct SPAux { virtual shared_ptr<SPAux> copy() const; }

struct VentureSP : VentureValue
{
  shared_ptr<PSP> requestPSP;
  shared_ptr<PSP> outputPSP;

  virtual shared_ptr<SPAux> constructSPAux() const;
  virtual shared_ptr<LatentDB> constructLatentDB() const;
  virtual void simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const;
  virtual double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  virtual bool hasAEKernel() const;
};

// TODO URGENT not sure when or how this is called yet.
struct SPRecord
{
  shared_ptr<SPFamilies> spFamilies;
  shared_ptr<SPAux> spAux;
  shared_ptr<VentureSP> sp;
};


#endif
