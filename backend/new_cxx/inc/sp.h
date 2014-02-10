#ifndef SP_H
#define SP_H

#include "types.h"
#include "value.h"
#include <map>

struct SPAux;
struct LSR;
struct LatentDB;

using std::map;

struct SPFamilies
{
  map<FamilyID,RootNodePtr> families;
  bool containsFamily(FamilyID id);
  Node * getFamily(FamilyID id);
  void registerFamily(FamilyID id,RootNodePtr root);
  void unregisterFamily(FamilyID id);
};

struct SPAux { virtual shared_ptr<SPAux> copy(); }

struct VentureSP : VentureValue
{
  shared_ptr<PSP> requestPSP;
  shared_ptr<PSP> outputPSP;

  shared_ptr<SPAux> constructSPAux();
  shared_ptr<LatentDB> constructLatentDB();
  void simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB);
  double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB);
  bool hasAEKernel();
};

struct SPRecord
{
  // TODO these could be unique pointers
  shared_ptr<SPFamilies> spFamilies;
  shared_ptr<SPAux> spAux;
  shared_ptr<VentureSP> sp;
}
#endif
