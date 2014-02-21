#ifndef PARTICLE_H
#define PARTICLE_H

#include "types.h"
#include "trace.h"
#include "smap.h"
#include "value.h"

#include "pset.h"
#include "pmap.h"

using persistent::PMap;
using persistent::PSet;

struct Particle : Trace
{
  Particle(ConcreteTrace * outerTrace);
  Particle(Particle * outerParticle);

/* Methods */

  /* Registering metadata */
  void registerAEKernel(Node * node);
  void registerUnconstrainedChoice(Node * node);
  void registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node);
  void registerConstrainedChoice(Node * node);

  /* Unregistering metadata */
  void unregisterAEKernel(Node * node);
  void unregisterUnconstrainedChoice(Node * node);
  void unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node);
  void unregisterConstrainedChoice(Node * node);

  /* Regen mutations */
  void addESREdge(RootOfFamily esrRoot,OutputNode * outputNode);
  void reconnectLookup(LookupNode * lookupNode);
  void incNumRequests(RootOfFamily root);
  void incRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  void addChild(Node * node, Node * child);

  /* Detach mutations */  
  RootOfFamily popLastESRParent(OutputNode * outputNode);
  void disconnectLookup(LookupNode * lookupNode);
  void decNumRequests(RootOfFamily root);
  void decRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  void removeChild(Node * node, Node * child);

  /* Primitive getters */
  VentureValuePtr getValue(Node * node);
  shared_ptr<SP> getMadeSP(Node * makerNode);
  shared_ptr<SPAux> getMadeSPAux(Node * makerNode);
  vector<RootOfFamily> getESRParents(Node * node);
  set<Node*> getChildren(Node * node);
  int getNumRequests(RootOfFamily root);
  int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node);

  VentureValuePtr getObservedValue(Node * node);

  bool isMakerNode(Node * node);
  bool isConstrained(Node * node);
  bool isObservation(Node * node);

  /* Primitive setters */
  void setValue(Node * node, VentureValuePtr value);
  void clearValue(Node * node);


  void setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord);
  void destroyMadeSPRecord(Node * makerNode);

  void setMadeSP(Node * makerNode,shared_ptr<SP> sp);
  void setMadeSPAux(Node * makerNode,shared_ptr<SPAux> spaux);

  void setChildren(Node * node,set<Node*> children);
  void setESRParents(Node * node,const vector<RootOfFamily> & esrRoots);

  void setNumRequests(Node * node,int num);

  /* SPFamily operations */
  void registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot);
  void unregisterMadeSPFamily(Node * makerNode,FamilyID id);

  bool containsMadeSPFamily(Node * makerNode, FamilyID id);
  RootOfFamily getMadeSPFamilyRoot(Node * makerNode, FamilyID id);

  /* Inference (computing reverse weight) */
  double logDensityOfBlock(ScopeID scope);
  int numBlocksInScope(ScopeID scope);

/* END methods */












/* Members */

  ConcreteTrace * baseTrace;
  
  /* Persistent data structures, with non-persistent analogs in ConcreteTrace */
  PSet<Node*> unconstrainedChoices;
  PSet<Node*> constrainedChoices;
  PSet<Node*> arbitraryErgodicKernels;

  PMap<DirectiveID,RootOfFamily> families;

  PMap<ScopeID,PMap<BlockID,PSet<Node*> > > scopes;

  PMap<Node*, vector<RootOfFamily> > esrRoots;
  PMap<RootOfFamily, int> numRequests;

  PMap<Node*,VentureValuePtr> values;
  PMap<Node*,shared_ptr<SP> > madeSPs;

  /* persistent, not stored in concrete trace */
  PMap<Node*, int> regenCounts;

  /* persistent additions */
  PMap<Node*, PMap<FamilyID,RootOfFamily> > newMadeSPFamilies;
  PMap<Node*,set<Node*> > newChildren;

  /* Non-persistent */
  map<Node*, shared_ptr<SPAux> > madeSPAuxs;


};



#endif
