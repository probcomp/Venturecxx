#include "db.h"
#include "value.h"
#include "values.h"

#include <boost/foreach.hpp>

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

void DB::addPartials(vector<Node*>& nodes, vector<VentureValuePtr>& partials) {
  assert(nodes.size() == partials.size());
  for(size_t i = 0; i < nodes.size(); i++) {
    Node* node = nodes[i];
    VentureValuePtr partial = partials[i];
    this->addPartial(node, partial);
  }
}

void DB::addPartial(Node* node, VentureValuePtr partial) {
  if(this->partials.count(node)) {
    cout << ::toString(this->partials[node]) << endl;
    cout << ::toString(partial) << endl;
    this->partials[node] = this->partials[node]+partial;
  }else{
    this->partials[node] = partial;
  }
}

VentureValuePtr DB::getPartial(Node* node) {
  if(this->partials.count(node) == 0) 
    this->partials[node] = VentureValuePtr(new VentureNumber(0));
  return this->partials[node];
}

vector<VentureValuePtr> DB::getPartials(const vector<Node*>& nodes) {
  vector<VentureValuePtr> res;
  BOOST_FOREACH(Node* node, nodes) {
    res.push_back(getPartial(node));
  }
  return res;
}