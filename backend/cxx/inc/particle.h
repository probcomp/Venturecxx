#ifndef PARTICLE_H
#define PARTICLE_H

#include <vector>
#include <map>
#include <set>
#include <deque>
#include "all.h"
#include "flush.h"

struct Trace;
struct Node;
struct LatentDB;
struct VentureValue;
enum class NodeType;

// TODO may need more fields, e.g. for constrain, owns value, etc
struct ParticleNode
{
  ParticleNode(Node * node,VentureValue * value): node(node), _value(value) {}
  ParticleNode(Node * node,Node * sourceNode): node(node), sourceNode(sourceNode) {}

  Node * node{nullptr};
  VentureValue * _value{nullptr};
  Node * sourceNode{nullptr};
};

struct DetachParticle : Trace
{
  bool isReference(Node * node);
  void registerReference(Node * node, Node * lookedUpNode);
  Node * getSourceNode(Node * node);
  void setSourceNode(Node * node, Node * sourceNode);
  void clearSourceNode(Node * node);

  void setValue(Node * node, VentureValue * value);
  void clearValue(Node * node);
  VentureValue * getValue(Node * node);

  SP * getSP(Node * node);
  VentureSP * getVSP(Node * node);
  SPAux * getSPAux(Node * node);
  SPAux * getMadeSPAux(Node * makerNode);
  Args getArgs(Node * node);
  vector<Node *> getESRParents(Node * node);
  
  void constrainChoice(Node * node);
  void unconstrainChoice(Node * node);

  void setConstrained(Node * node);
  void clearConstrained(Node * node);
  void setNodeOwnsValue(Node * node,bool giveOwnershipToSP);

  Node * removeLastESREdge(Node * outputNode);
  void addESREdge(Node * esrParent,Node * outputNode);

  void detachMadeSPAux(Node * makerNode);


  void preUnabsorb(Node * node) {}
  void preAbsorb(Node * node) {}
  void preUnapplyPSP(Node * node) {}
  void preApplyPSP(Node * node) {}
  void preUnevalRequests(Node * requestNode) {}
  void preEvalRequests(Node * requestNode) {}
  void preUnconstrain(Node * node) {}
  void preConstrain(Node * node) {}

  void extractLatentDB(SP * sp,LatentDB * latentDB);
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType);
  void extractValue(Node * node, VentureValue * value);
  void prepareLatentDB(SP * sp);
  LatentDB * getLatentDB(SP * sp);
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB);

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values);
  void registerSPFamily(Node * makerNode,size_t id,Node * root);

////////////////////////

  map<Node *, ParticleNode> pnodes;
  map<Node *, vector<Node *> > children;
  map<Node*,SPAux*> spauxs;

  set<Node *> randomChoices;
  set<Node *> constrainedChoices;

  deque<FlushEntry> flushDeque; // detach uses queue, regen uses stack
  set<Node *> random

  Trace * trace{nullptr};
};













#endif
