#ifndef PARTICLE_H
#define PARTICLE_H

#include <vector>
#include <map>
#include <set>
#include <deque>
#include <stack>
#include "all.h"
#include "flush.h"
#include "trace.h"


struct Node;
struct LatentDB;
struct VentureValue;
struct VentureSP;

enum class NodeType;

struct Particle : Trace
{

  Particle(Trace * trace): trace(trace) {}

  void commit();

  multimap<Node *, Node *> children;
  map<Node*,SPAux*> spauxs;
  map<Node *,VentureValue*> values;
  map<Node *, Node *> sourceNodes;

  vector<VentureValue*> spOwnedValues;

  set<Node *> crcs;
  set<Node *> rcs;

  map<VentureSP *,Node*> vspMakerNodes;

  map<Node*,stack<Node *> > esrParents;

  deque<FlushEntry> flushDeque; // detach uses queue, regen uses stack

///////////////////// Methods that by default will assert(false)

  bool isReference(Node * node) override { assert(false); }
  void registerReference(Node * node, Node * lookedUpNode) override { assert(false); }
  Node * getSourceNode(Node * node) override { assert(false); }
  void setSourceNode(Node * node, Node * sourceNode) override { assert(false); }
  void clearSourceNode(Node * node) override { assert(false); }

  void disconnectLookup(Node * node) override { assert(false); }
  void reconnectLookup(Node * node) override { assert(false); }
  void connectLookup(Node * node, Node * lookedUpNode) override { assert(false); }

  void setValue(Node * node, VentureValue * value) override { assert(false); }
  void clearValue(Node * node) override { assert(false); }
  VentureValue * getValue(Node * node) override { assert(false); }

  SP * getSP(Node * node) override { assert(false); }
  VentureSP * getVSP(Node * node) override { assert(false); }
  SPAux * getSPAux(Node * node) override { assert(false); }
  SPAux * getMadeSPAux(Node * makerNode) override { assert(false); }
  Args getArgs(Node * node) override { assert(false); }
  vector<Node *> getESRParents(Node * node) override { assert(false); }
  
  void constrainChoice(Node * node) override { assert(false); }
  void unconstrainChoice(Node * node) override { assert(false); }

  void registerRandomChoice(Node * node) override { assert(false); }
  void unregisterRandomChoice(Node * node) override { assert(false); }


  void setConstrained(Node * node) override { assert(false); }
  void clearConstrained(Node * node) override { assert(false); }
  void setNodeOwnsValue(Node * node) override { assert(false); }
  void clearNodeOwnsValue(Node * node) override { assert(false); }

  Node * removeLastESREdge(Node * outputNode) override { assert(false); }
  void addESREdge(Node * esrParent,Node * outputNode) override { assert(false); }

  void detachMadeSPAux(Node * makerNode) override { assert(false); }


  void preUnabsorb(Node * node) override { assert(false); }
  void preAbsorb(Node * node) override { assert(false); }
  void preUnapplyPSP(Node * node) override { assert(false); }
  void preApplyPSP(Node * node) override { assert(false); }
  void preUnevalRequests(Node * requestNode) override { assert(false); }
  void preEvalRequests(Node * requestNode) override { assert(false); }
  void preUnconstrain(Node * node) override { assert(false); }
  void preConstrain(Node * node) override { assert(false); }
  void clearVSPMakerNode(Node * node) override { assert(false); }
  void setVSPMakerNode(Node * node) override { assert(false); }

  void extractLatentDB(SP * sp,LatentDB * latentDB) override { assert(false); }
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override { assert(false); }
  void extractValue(Node * node, VentureValue * value) override { assert(false); }
  void prepareLatentDB(SP * sp) override { assert(false); }
  LatentDB * getLatentDB(SP * sp) override { assert(false); }
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB) override { assert(false); }

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override { assert(false); }
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override { assert(false); }
////////////////

  Trace * trace;

  virtual ~Particle() {}
};

struct DetachParticle : Particle
{
  DetachParticle(Trace * trace): Particle(trace) {}

  void maybeCloneSPAux(Node * node);
  void maybeCloneMadeSPAux(Node * makerNode);

  bool isReference(Node * node) override;
  Node * getSourceNode(Node * node) override;
  void clearSourceNode(Node * node) override;

  void disconnectLookup(Node * node) override;

  void clearValue(Node * node) override;
  VentureValue * getValue(Node * node) override;

  SP * getSP(Node * node) override;
  VentureSP * getVSP(Node * node) override;
  SPAux * getSPAux(Node * node) override;
  SPAux * getMadeSPAux(Node * makerNode) override;
  Args getArgs(Node * node) override;
  vector<Node *> getESRParents(Node * node) override;
  
  void unconstrainChoice(Node * node) override;

  void unregisterRandomChoice(Node * node) override;


  void clearConstrained(Node * node) override;
  void setNodeOwnsValue(Node * node) override;

  Node * removeLastESREdge(Node * outputNode) override;

  void detachMadeSPAux(Node * makerNode) override;


  void preUnabsorb(Node * node) override;
  void preUnapplyPSP(Node * node) override;
  void preUnevalRequests(Node * requestNode) override;
  void preUnconstrain(Node * node) override;

  void clearVSPMakerNode(Node * node) override;

  void extractLatentDB(SP * sp,LatentDB * latentDB) override;
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override;
  void extractValue(Node * node, VentureValue * value) override;
  void prepareLatentDB(SP * sp) override;
  LatentDB * getLatentDB(SP * sp) override;
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB) override;

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override;
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override;

////////////////////////


};

struct RegenParticle : Particle
{
  RegenParticle(Trace * trace): Particle(trace) {}


  bool isReference(Node * node) override;
  void registerReference(Node * node, Node * lookedUpNode) override;
  Node * getSourceNode(Node * node) override;
  void setSourceNode(Node * node, Node * sourceNode) override;
  void clearSourceNode(Node * node) override;

  void disconnectLookup(Node * node) override;
  void reconnectLookup(Node * node) override;
  void connectLookup(Node * node, Node * lookedUpNode) override;

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
  void clearVSPMakerNode(Node * node) override;
  void setVSPMakerNode(Node * node) override;

  void extractLatentDB(SP * sp,LatentDB * latentDB) override;
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override;
  void extractValue(Node * node, VentureValue * value) override;
  void prepareLatentDB(SP * sp) override;
  LatentDB * getLatentDB(SP * sp) override;
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB) override;

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override;
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override;

////////////////////////


};












#endif
