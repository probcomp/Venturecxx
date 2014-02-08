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
  map<FamilyID,RootOfFamily> families;
  bool containsFamily(FamilyID id);
  Node * getFamily(FamilyID id);
  void registerFamily(FamilyID id,RootOfFamily root);
  void unregisterFamily(FamilyID id);
};

struct SPAux { virtual SPAux * copy(); }

struct VentureSP : VentureValue
{
  PSP * requestPSP;
  PSP * outputPSP;

  SPAux * constructSPAux();
  LatentDB * constructLatentDB();
  void simulateLatents(SPAux * spaux,LSR * lsr,bool shouldRestore,LatentDB * latentDB);
  double detachLatents(SPAux * spaux,LSR * lsr,LatentDB * latentDB);
  bool hasAEKernel();
};

struct SPRecord
{
  SPFamilies * spFamilies;
  SPAux * spAux;
  VentureSP * sp;
}
#endif
