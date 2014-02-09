#ifndef TRACE_H
#define TRACE_H

#include "types.h"
#include <set>
#include <map>
#include <vector>
#include "smap.h"

using std::set;
using std::map;
using std::vector;

struct Node;

struct Trace 
{
  /* Registering metadata */
  virtual void registerAEKernel(Node * node) =0;
  virtual void registerRandomChoice(Node * node) =0;
  virtual void registerRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void registerConstrainedChoice(Node * node) =0;

  /* Unregistering metadata */
  virtual void unregisterAEKernel(Node * node) =0;
  virtual void unregisterRandomChoice(Node * node) =0;
  virtual void unregisterRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void unregisterConstrainedChoice(Node * node) =0;

  /* Creating nodes */
  ConstantNode * createConstantNode(VentureValuePtr);
  LookupNode * createLookupNode(Node * sourceNode);
  pair<RequestNode*,OutputNode*> createApplicationNodes(Node *operatorNode,const vector<Node*> & operandNodes,VentureEnvironmentPtr env);

  /* Regen mutations */
  void addESREdge(Node *esrParent,OutputNode * outputNode);
  void reconnectLookup(LookupNode * lookupNode);
  void incNumRequests(Node * node);
  void addChild(Node * node, Node * child);

  /* Detach mutations */  
  Node * popLastESRParent(OutputNode * outputNode);
  void disconnectLookup(LookupNode * lookupNode);
  void decNumRequests(Node * node);
  def removeChild(Node * node, Node * child);

  /* Primitive getters */
  VentureValuePtr getValue(Node * node);
  SPRecord getMadeSPRecord(OutputNode * makerNode);
  vector<Node*> getESRParents(Node * node);
  set<Node*> getChildren(Node * node);
  int getNumRequests(Node * node);
  int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  VentureValuePtr getObservedValue(Node * node);

  bool isConstrained(Node * node);
  bool isObservation(Node * node);

  /* Derived getters (just for convenience)*/
  VentureValuePtr getGroundValue(Node * node);
  Node * getSPMakerNode(Node * node);
  shared_ptr<SPRef> getSPRef(Node * node);
  shared_ptr<VentureSP> getSP(Node * node);
  shared_ptr<SPFamilies> getSPFamilies(Node * node);
  shared_ptr<SPAux> getSPAux(Node * node);
  shared_ptr<PSP> getPSP(Node * node);
  vector<Node*> getParents(Node * node);

  /* Primitive setters */
  void setValue(Node * node, VentureValuePtr value);
  void clearValue(Node * node);

  void createSPRecord(OutputNode * makerNode); // No analogue in VentureLite

  void initMadeSPFamilies(Node * node);
  void clearMadeSPFamilies(Node * node);

  void setMadeSP(Node * node,shared_ptr<VentureSP> sp);
  void setMadeSPAux(Node * node,shared_ptr<SPAux> spaux);

  void setChildren(Node * node,set<Node*> children);
  void setESRParents(Node * node,const vector<Node*> & esrParents);

  void setNumRequests(Node * node,int num);

  /* SPFamily operations */
  // Note: this are different from current VentureLite, since it does not automatically jump
  // from a node to its spmakerNode. (motivation: avoid confusing non-commutativity in particles)
  void registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent);
  void unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent);
  bool containsMadeSPFamily(OutputNode * makerNode, FamilyID id);
  Node * getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id);

};

struct ConcreteTrace : Trace
{
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
  void addRandomChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node);

  bool scopeHasEntropy(ScopeID scope); 
  void makeConsistent();
  Node * getOutermostNonRefAppNode(Node * node);

  int numRandomChoices();

  int getSeed();
  double getGlobalLogScore();

  // Helpers for particle commit
  void addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies);
  void addNewChildren(Node * node,PSet newChildren);

private:
  VentureEnvironment * globalEnvironment;
  set<Node*> unconstrainedRandomChoices;
  set<Node*> constrainedChoices;
  set<Node*> arbitraryErgodicKernels;
  set<Node*> unpropagatedObservations;
  map<DirectiveID,RootNodePtr> families;
  map<ScopeID,SMap<BlockID,set<Node*> > scopes;

  map<Node*, vector<Node*> > esrParents;
  map<Node*, int> numRequests;
  map<Node*, SPRecord> madeSPRecords;
  map<Node*,set<Node*> > children;
  map<Node*,VentureValuePtr> observedValues;


};

#endif
