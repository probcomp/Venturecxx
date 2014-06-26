#include "db.h"

bool DB::hasValue(Node * node) { return values.count(node); }

VentureValuePtr DB::getValue(Node * node)
{
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
  return latentDBs.count(makerNode);
}

shared_ptr<LatentDB> DB::getLatentDB(Node * makerNode)
{
  assert(latentDBs.count(makerNode));
  return latentDBs[makerNode];
}

void DB::registerLatentDB(Node * makerNode, shared_ptr<LatentDB> latentDB)
{
  assert(!latentDBs.count(makerNode));
  latentDBs[makerNode] = latentDB;
}

bool DB::hasESRParent(shared_ptr<SP> sp,FamilyID id)
{
  return spFamilyDBs[sp].count(id);
}

RootOfFamily DB::getESRParent(shared_ptr<SP> sp,FamilyID id)
{
  assert(spFamilyDBs[sp].count(id));
  return spFamilyDBs[sp][id];
}

void DB::registerSPFamily(shared_ptr<SP> sp,FamilyID id,RootOfFamily esrParent)
{
  assert(!spFamilyDBs[sp].count(id));
  spFamilyDBs[sp][id] = esrParent;
}

bool DB::hasMadeSPAux(Node * makerNode) { return spAuxs.count(makerNode); }

shared_ptr<SPAux> DB::getMadeSPAux(Node * makerNode)
{
  assert(spAuxs.count(makerNode));
  return spAuxs[makerNode];
}

void DB::registerMadeSPAux(Node * makerNode, shared_ptr<SPAux> spAux)
{
  assert(!spAuxs.count(makerNode));
  spAuxs[makerNode] = spAux;
}
