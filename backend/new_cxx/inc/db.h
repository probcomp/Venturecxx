#ifndef DB_H
#define DB_H

#include "types.h"

struct OutputNode;

struct LatentDB { virtual ~LatentDB() {}; };

struct DB
{
  bool hasValue(Node * node);
  VentureValuePtr getValue(Node * node);
  void registerValue(Node * node, VentureValuePtr value);

  bool hasLatentDB(OutputNode * makerNode);
  shared_ptr<LatentDB> getLatentDB(OutputNode * makerNode);
  void registerLatentDB(OutputNode * makerNode, shared_ptr<LatentDB> latentDB);

  RootOfFamily getESRParent(shared_ptr<VentureSP> sp,FamilyID id);
  void registerSPFamily(shared_ptr<VentureSP> sp,FamilyID id,RootOfFamily esrParent);

private:
  map<OutputNode*,shared_ptr<LatentDB> > latentDBs;
  map<Node*,VentureValuePtr> values;
  map<shared_ptr<VentureSP>,map<FamilyID,RootOfFamily> > spFamilyDBs;
  
};

#endif
