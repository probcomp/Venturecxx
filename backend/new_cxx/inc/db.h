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
  void hasLatentDB(OutputNode * makerNode);
  void registerLatentDB(OutputNode * makerNode, shared_ptr<LatentDB> latentDB);

  Node * getESRParent(VentureSPPtr sp,FamilyID id);
  void registerSPFamily(VentureSPPtr sp,FamilyID id,Node * esrParent);

private:
  map<Node*,shared_ptr<LatentDB> > latentDBs;
  map<OutputNode*,VentureValuePtr> values;
  map<shared_ptr<SP>,map<FamilyID,RootNodePtr> > spFamilyDBs;
  
};

#endif
