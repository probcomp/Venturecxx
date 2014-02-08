#ifndef DB_H
#define DB_H

struct LatentDB { virtual ~LatentDB() {}; };

struct DB
{
  bool hasValue(Node * node);
  VentureValuePtr registerValue(Node * node);
  void extractValue(Node * node, VentureValuePtr value);

  bool hasLatentDB(Node * node);
  void registerLatentDB(Node * node, VentureValuePtr value);

  Node * getESRParent(VentureSPPtr sp,FamilyID id);
  void registerSPFamily(VentureSPPtr sp,FamilyID id,Node * esrParent);

private:
  map<Node*,shared_ptr<LatentDB> > latentDBs;
  map<Node*,VentureValuePtr> values;
  map<Node*,map<FamilyID,RootNodePtr> > spFamilyDBs;
  
};

#endif
