#ifndef CONCRETE_TRACE_H
#define CONCRETE_TRACE_H

#include "types.h"
#include "trace.h"

struct ConcreteTrace : Trace
{
  /* TODO once we pass particle tests and care about supporting people, we will remove "override" keywords */

  /* Registering metadata */
  void registerAEKernel(Node * node) override;
  void registerUnconstrainedChoice(Node * node) override;
  void registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) override;
  void registerConstrainedChoice(Node * node) override;

  /* Unregistering metadata */
  void unregisterAEKernel(Node * node) override;
  void unregisterUnconstrainedChoice(Node * node) override;
  void unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) override;
  void unregisterConstrainedChoice(Node * node) override;

  /* Regen mutations */
  void addESREdge(Node *esrParent,OutputNode * outputNode) override;
  void reconnectLookup(LookupNode * lookupNode) override;
  void incNumRequests(Node * node) override;
  void addChild(Node * node, Node * child) override;

  /* Detach mutations */  
  Node * popLastESRParent(OutputNode * outputNode) override;
  void disconnectLookup(LookupNode * lookupNode) override;
  void decNumRequests(Node * node) override;
  void removeChild(Node * node, Node * child) override;

  /* Primitive getters */
  VentureValuePtr getValue(Node * node) override;
  SPRecord getMadeSPRecord(OutputNode * makerNode) override;
  vector<Node*> getESRParents(Node * node) override;
  set<Node*> getChildren(Node * node) override;
  int getNumRequests(Node * node) override;
  int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) override;
  VentureValuePtr getObservedValue(Node * node) override;

  bool isConstrained(Node * node) override;
  bool isObservation(Node * node) override;

  /* Primitive Setters */
  void setValue(Node * node, VentureValuePtr value) override;
  void clearValue(Node * node) override;

  void createSPRecord(OutputNode * makerNode) override; // No analogue in VentureLite

  void initMadeSPFamilies(Node * node) override;
  void clearMadeSPFamilies(Node * node) override;

  void setMadeSP(Node * node,shared_ptr<VentureSP> sp) override;
  void setMadeSPAux(Node * node,shared_ptr<SPAux> spaux) override;

  void setChildren(Node * node,set<Node*> children) override;
  void setESRParents(Node * node,const vector<Node*> & esrParents) override;

  void setNumRequests(Node * node,int num) override;

  /* SPFamily operations */
  void registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent) override;
  void unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent) override;
  bool containsMadeSPFamily(OutputNode * makerNode, FamilyID id) override;
  Node * getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id) override;


  /* New in ConcreteTrace */

  BlockID sampleBlock(ScopeID scope);
  double logDensityOfBlock(ScopeID scope);
  vector<BlockID> blocksInScope(ScopeID scope); // TODO this should be an iterator
  int numBlocksInScope(ScopeID scope);
  set<Node*> getAllNodesInScope(ScopeID scope);
    
  vector<set<Node*> > getOrderedSetsInScope(ScopeID scope);

  // TODO Vlad: read this carefully. The default scope is handled differently than the other scopes.
  // For default, the nodes are the actualy principal nodes.
  // For every other scope, they are only the roots w.r.t. the dynamic scoping rules.
  set<Node*> getNodesInBlock(ScopeID scope, BlockID block);

  // Helper function for dynamic scoping
  void addUnconstrainedChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node);

  bool scopeHasEntropy(ScopeID scope); 
  void makeConsistent();
  Node * getOutermostNonRefAppNode(Node * node);

  int numUnconstrainedChoices();

  int getSeed();
  double getGlobalLogScore();

  // Helpers for particle commit
  //void addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies);
  //void addNewChildren(Node * node,PSet newChildren);

private:
  VentureEnvironment * globalEnvironment;
  set<Node*> unconstrainedChoices;
  set<Node*> constrainedChoices;
  set<Node*> arbitraryErgodicKernels;

  set<Node*> unpropagatedObservations;

  map<DirectiveID,RootOfFamily> families;

  //map<ScopeID,SamplableMap<BlockID,set<Node*> > scopes; // VLAD skip everything that touches this

  map<Node*, vector<Node*> > esrParents;
  map<Node*, int> numRequests;
  map<Node*, SPRecord> madeSPRecords;
  map<Node*,set<Node*> > children;
  map<Node*,VentureValuePtr> values;
  map<Node*,VentureValuePtr> observedValues;

};

#endif
