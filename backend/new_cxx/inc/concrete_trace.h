#ifndef CONCRETE_TRACE_H
#define CONCRETE_TRACE_H

#include "types.h"
#include "trace.h"
#include "smap.h"
#include "value.h"

struct ConcreteTrace : Trace
{
  ConcreteTrace();
  /* TODO once we pass particle tests and care about supporting people, we will remove "override" keywords */

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
  vector<RootOfFamily> getESRParents(Node * node);
  set<Node*> getChildren(Node * node);
  int getNumRequests(RootOfFamily root);
  int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  VentureValuePtr getObservedValue(Node * node);
  shared_ptr<SP> getMadeSP(Node * makerNode);
  shared_ptr<SPFamilies> getMadeSPFamilies(Node * makerNode);

  shared_ptr<SPAux> getMadeSPAux(Node * makerNode);
  shared_ptr<VentureSPRecord> getMadeSPRecord(Node * makerNode); // not in particle


  bool isMakerNode(Node * node);
  bool isConstrained(Node * node);
  bool isObservation(Node * node);

  /* Primitive Setters */
  void setValue(Node * node, VentureValuePtr value);
  void clearValue(Node * node);

  void observeNode(Node * node,VentureValuePtr value);

  void setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord);
  void destroyMadeSPRecord(Node * makerNode);


  void clearMadeSPFamilies(Node * node);
  

  void setMadeSP(Node * node,shared_ptr<SP> sp);
  void setMadeSPAux(Node * node,shared_ptr<SPAux> spaux);

  void setChildren(Node * node,set<Node*> children);
  void setESRParents(Node * node,const vector<RootOfFamily> & esrRoots);

  void setNumRequests(Node * node,int num);

  /* SPFamily operations */
  void registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot);
  void unregisterMadeSPFamily(Node * makerNode,FamilyID id);

  bool containsMadeSPFamily(Node * makerNode, FamilyID id);
  RootOfFamily getMadeSPFamilyRoot(Node * makerNode, FamilyID id);



  /* New in ConcreteTrace */

  BlockID sampleBlock(ScopeID scope);
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

  int numUnconstrainedChoices();

  int getSeed();
  double getGlobalLogScore();

  // Helpers for particle commit
  //void addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies);
  //void addNewChildren(Node * node,PSet newChildren);

  shared_ptr<VentureEnvironment> globalEnvironment;

  set<Node*> unconstrainedChoices;
  set<Node*> constrainedChoices;
  set<Node*> arbitraryErgodicKernels;

  map<Node*,VentureValuePtr> unpropagatedObservations;

  map<DirectiveID,RootOfFamily> families;

  VentureValuePtrMap<SamplableMap<BlockID,set<Node*> > > scopes;

  map<Node*, vector<RootOfFamily> > esrRoots;
  map<RootOfFamily, int> numRequests;
  map<Node*, shared_ptr<VentureSPRecord> > madeSPRecords;
  map<Node*,set<Node*> > children;
  map<Node*,VentureValuePtr> values;
  map<Node*,VentureValuePtr> observedValues;

};

#endif
