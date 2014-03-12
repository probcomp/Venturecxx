#include "db.h"

typedef boost::shared_lock<boost::shared_mutex> ReaderLock;
typedef boost::upgrade_lock<boost::shared_mutex> UpgradeLock;
typedef boost::upgrade_to_unique_lock<boost::shared_mutex> UpgradeToUniqueLock;


bool DB::hasValue(Node * node) 
{ 
  ReaderLock l(_mutex_values);
  return values.count(node); 
}

VentureValuePtr DB::getValue(Node * node)
{
  ReaderLock l(_mutex_values);
  assert(values.count(node));
  return values[node];
}

void DB::registerValue(Node * node,VentureValuePtr value)
{
  assert(!values.count(node));
  values[node] = value;
}

bool DB::hasLatentDB(Node * makerNode)
{
  ReaderLock l(_mutex_latentDBs);
  return latentDBs.count(makerNode);
}

shared_ptr<LatentDB> DB::getLatentDB(Node * makerNode)
{
  ReaderLock l(_mutex_latentDBs);
  assert(latentDBs.count(makerNode));
  return latentDBs[makerNode];
}

void DB::registerLatentDB(Node * makerNode, shared_ptr<LatentDB> latentDB)
{
  UpgradeLock l(_mutex_latentDBs);
  UpgradeToUniqueLock ll(l);

  assert(!latentDBs.count(makerNode));
  latentDBs[makerNode] = latentDB;
}

RootOfFamily DB::getESRParent(shared_ptr<SP> sp,FamilyID id)
{
  ReaderLock l(_mutex_spFamilyDBs);
  assert(spFamilyDBs[sp].count(id));
  return spFamilyDBs[sp][id];
}

void DB::registerSPFamily(shared_ptr<SP> sp,FamilyID id,RootOfFamily esrParent)
{
  UpgradeLock l(_mutex_spFamilyDBs);
  UpgradeToUniqueLock ll(l);

  assert(!spFamilyDBs[sp].count(id));
  spFamilyDBs[sp][id] = esrParent;
}

bool DB::hasMadeSPAux(Node * makerNode) 
{
  ReaderLock l(_mutex_spAuxs);
  return spAuxs.count(makerNode); 
}

shared_ptr<SPAux> DB::getMadeSPAux(Node * makerNode)
{
  ReaderLock l(_mutex_spAuxs);
  assert(spAuxs.count(makerNode));
  return spAuxs[makerNode];
}

void DB::registerMadeSPAux(Node * makerNode, shared_ptr<SPAux> spAux)
{
  UpgradeLock l(_mutex_spAuxs);
  UpgradeToUniqueLock ll(l);

  assert(!spAuxs.count(makerNode));
  spAuxs[makerNode] = spAux;
}
