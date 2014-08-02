#ifndef DB_H
#define DB_H

#include "types.h"

struct OutputNode;
struct SPAux;
struct SP;
struct Node;

struct LatentDB { virtual ~LatentDB() {}; };

struct DB
{
  virtual bool hasValue(Node * node);
  virtual VentureValuePtr getValue(Node * node);
  virtual void registerValue(Node * node, VentureValuePtr value);

  bool hasLatentDB(Node * makerNode);
  shared_ptr<LatentDB> getLatentDB(Node * makerNode);
  void registerLatentDB(Node * makerNode, shared_ptr<LatentDB> latentDB);

  bool hasESRParent(shared_ptr<SP> sp,FamilyID id);
  RootOfFamily getESRParent(shared_ptr<SP> sp,FamilyID id);
  void registerSPFamily(shared_ptr<SP> sp,FamilyID id,RootOfFamily esrParent);

  bool hasMadeSPAux(Node * makerNode);
  shared_ptr<SPAux> getMadeSPAux(Node * makerNode);
  void registerMadeSPAux(Node * makerNode, shared_ptr<SPAux> spAux);

private:
  map<Node*,shared_ptr<LatentDB> > latentDBs;
  map<Node*,VentureValuePtr> values;
  map<shared_ptr<SP>,map<FamilyID,RootOfFamily> > spFamilyDBs;
  map<Node*,shared_ptr<SPAux> > spAuxs;
};

#endif
