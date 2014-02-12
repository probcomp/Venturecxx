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

bool DB::hasLatentDB(OutputNode * makerNode)
{
  return latentDBs.count(makerNode);
}

shared_ptr<LatentDB> DB::getLatentDB(OutputNode * makerNode)
{
  assert(latentDBs.count(makerNode));
  return latentDBs[makerNode];
}

void DB::registerLatentDB(OutputNode * makerNode, shared_ptr<LatentDB> latentDB)
{
  assert(!latentDBs.count(makerNode));
  latentDBs[makerNode] = latentDB;
}

RootOfFamily DB::getESRParent(shared_ptr<VentureSP> sp,FamilyID id)
{
  assert(spFamilyDBs[sp].count(id));
  return spFamilyDBs[sp][id];
}

void DB::registerSPFamily(shared_ptr<VentureSP> sp,FamilyID id,RootOfFamily esrParent)
{
  assert(!spFamilyDBs[sp].count(id));
  spFamilyDBs[sp][id] = esrParent;
}

