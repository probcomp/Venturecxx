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

  void maybeCloneSPAux(Node * node);
  void maybeCloneMadeSPAux(Node * makerNode);
  void commit();

  multimap<Node *, Node *> children;
  map<Node*,SPAux*> spauxs;
  map<Node *,VentureValue*> values;
  map<Node *, Node *> sourceNodes;

  vector<VentureValue*> spOwnedValues;

  set<Node *> crcs;
  set<Node *> rcs;

  map<VentureSP *,Node*> vspMakerNodes;

  map<Node*,vector<Node *> > esrParents;

  deque<FlushEntry> flushDeque; // detach uses queue, regen uses stack


  Trace * trace;

  virtual ~Particle() {}
};

struct DetachParticle : Particle
{
  DetachParticle(Trace * trace): Particle(trace) {}

//  RegenParticle cloneAsRegenParticle() { }

////

  void clearSourceNode(Node * node) override;

  void disconnectLookup(Node * node) override;

  void unconstrainChoice(Node * node) override;

  void unregisterRandomChoice(Node * node) override;

  Node * removeLastESREdge(Node * outputNode) override;

  void detachMadeSPAux(Node * makerNode) override;




  void preUnabsorb(Node * node) override;
  void preUnapplyPSP(Node * node) override;

  void preUnconstrain(Node * node) override;

  void clearVSPMakerNode(Node * node) override;

  void extractLatentDB(SP * sp,LatentDB * latentDB) override;
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override;
  void extractValue(Node * node, VentureValue * value) override;
  void prepareLatentDB(SP * sp) override; // once omegaDB extends trace, this no-op will be default
  LatentDB * getLatentDB(SP * sp) override;
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB) override;

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override;
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override;


};

struct RegenParticle : Particle
{
  RegenParticle(Trace * trace): Particle(trace) {}

  Node * getSourceNode(Node * node) override;
  void setSourceNode(Node * node, Node * sourceNode) override;

  void connectLookup(Node * node, Node * lookedUpNode) override;

  void setValue(Node * node, VentureValue * value) override;
  VentureValue * getValue(Node * node) override;

  SPAux * getSPAux(Node * node) override;
  SPAux * getMadeSPAux(Node * makerNode) override;
  vector<Node *> getESRParents(Node * node) override;
  
  void constrainChoice(Node * node) override;

  void registerRandomChoice(Node * node) override;

  void setConstrained(Node * node);
  void clearNodeOwnsValue(Node * node);

  void addESREdge(Node * esrParent,Node * outputNode) override;

  void preAbsorb(Node * node) override;
  void preApplyPSP(Node * node) override;



  void setVSPMakerNode(Node * node) override;
  void regenMadeSPAux(Node * makerNode, SP * sp);

  // TODO URGENT not sure when this should be called in regen
  // probably needs to be a different method
  // for now: memory leak
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType) override;

  
  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values) override;
  void registerSPFamily(Node * makerNode,size_t id,Node * root) override;

////////////////////////


};












#endif
