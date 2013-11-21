#ifndef PARTICLE_H
#define PARTICLE_H

#include <vector>
#include <map>
#include <set>
#include <deque>
#include "all.h"
#include "flush.h"
#include "trace.h"


struct Node;
struct LatentDB;
struct VentureValue;

enum class NodeType;

// TODO may need more fields, e.g. for constrain, owns value, etc
struct ParticleNode
{
  ParticleNode() {}
  ParticleNode(Node * node,VentureValue * value): node(node), _value(value) {}
  ParticleNode(Node * node,Node * sourceNode): node(node), sourceNode(sourceNode) {}

  Node * node{nullptr};
  VentureValue * _value{nullptr};
  vector<Node *> esrParents{};
  Node * sourceNode{nullptr};
};

struct DetachParticle : Trace
{
  DetachParticle(Trace * trace): trace(trace) {}

  void maybeCloneSPAux(Node * node);
  void maybeCloneMadeSPAux(Node * makerNode);

  bool isReference(Node * node) override;
  void registerReference(Node * node, Node * lookedUpNode) override;
  Node * getSourceNode(Node * node) override;
  void setSourceNode(Node * node, Node * sourceNode) override;
  void clearSourceNode(Node * node) override;

  void setValue(Node * node, VentureValue * value) override;
  void clearValue(Node * node) override;
  VentureValue * getValue(Node * node) override;

  SP * getSP(Node * node) override;
  VentureSP * getVSP(Node * node) override;
  SPAux * getSPAux(Node * node) override;
  SPAux * getMadeSPAux(Node * makerNode) override;
  Args getArgs(Node * node) override;
  vector<Node *> getESRParents(Node * node) override;
  
  void constrainChoice(Node * node) override;
  void unconstrainChoice(Node * node) override;

  void registerRandomChoice(Node * node) override;
  void unregisterRandomChoice(Node * node) override;


  void setConstrained(Node * node) override;
  void clearConstrained(Node * node) override;
  void setNodeOwnsValue(Node * node) override;
  void clearNodeOwnsValue(Node * node) override;

  Node * removeLastESREdge(Node * outputNode) override;
  void addESREdge(Node * esrParent,Node * outputNode) override;

  void detachMadeSPAux(Node * makerNode) override;


  void preUnabsorb(Node * node) override;
  void preAbsorb(Node * node) override;
  void preUnapplyPSP(Node * node) override;
  void preApplyPSP(Node * node) override;
  void preUnevalRequests(Node * requestNode) override;
  void preEvalRequests(Node * requestNode) override;
  void preUnconstrain(Node * node) override;
  void preConstrain(Node * node) override;

  void extractLatentDB(SP * sp,LatentDB * latentDB) override;
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override;
  void extractValue(Node * node, VentureValue * value) override;
  void prepareLatentDB(SP * sp) override;
  LatentDB * getLatentDB(SP * sp) override;
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB) override;

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override;
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override;

////////////////////////

  map<Node *, ParticleNode> pnodes;
  map<Node *, vector<Node *> > children;
  map<Node*,SPAux*> spauxs;

  vector<VentureValue*> spOwnedValues;

  set<Node *> crcs;
  set<Node *> rcs;

  deque<FlushEntry> flushDeque; // detach uses queue, regen uses stack


  Trace * trace{nullptr};
};













#endif
