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
  virtual ConstantNode * createConstantNode(VentureValuePtr);
  virtual LookupNode * createLookupNode(Node * sourceNode);
  virtual pair<RequestNode*,OutputNode*> createApplicationNodes(Node *operatorNode,const vector<Node*> & operandNodes,VentureEnvironmentPtr env);

  /* Regen mutations */
  virtual void addESREdge(Node *esrParent,OutputNode * outputNode);
  virtual void reconnectLookup(LookupNode * lookupNode);
  virtual void incNumRequests(Node * node);
  virtual void addChild(Node * node, Node * child);

  /* Detach mutations */  
  virtual Node * popLastESRParent(OutputNode * outputNode);
  virtual void disconnectLookup(LookupNode * lookupNode);
  virtual void decNumRequests(Node * node);
  virtual def removeChild(Node * node, Node * child);

  /* Primitive getters */
  virtual VentureValuePtr getValue(Node * node);
  virtual SPRecord getMadeSPRecord(OutputNode * makerNode);
  virtual vector<Node*> getESRParents(Node * node);
  virtual set<Node*> getChildren(Node * node);
  virtual int getNumRequests(Node * node);
  virtual int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node);
  virtual VentureValuePtr getObservedValue(Node * node);

  virtual bool isConstrained(Node * node);
  virtual bool isObservation(Node * node);

  /* Derived getters (just for convenience)*/
  virtual VentureValuePtr getGroundValue(Node * node);
  virtual Node * getSPMakerNode(Node * node);
  virtual shared_ptr<SPRef> getSPRef(Node * node);
  virtual shared_ptr<VentureSP> getSP(Node * node);
  virtual shared_ptr<SPFamilies> getSPFamilies(Node * node);
  virtual shared_ptr<SPAux> getSPAux(Node * node);
  virtual shared_ptr<PSP> getPSP(Node * node);
  virtual vector<Node*> getParents(Node * node);

  /* Primitive setters */
  virtual void setValue(Node * node, VentureValuePtr value);
  virtual void clearValue(Node * node);

  virtual void createSPRecord(OutputNode * makerNode); // No analogue in VentureLite

  virtual void initMadeSPFamilies(Node * node);
  virtual void clearMadeSPFamilies(Node * node);

  virtual void setMadeSP(Node * node,shared_ptr<VentureSP> sp);
  virtual void setMadeSPAux(Node * node,shared_ptr<SPAux> spaux);

  virtual void setChildren(Node * node,set<Node*> children);
  virtual void setESRParents(Node * node,const vector<Node*> & esrParents);

  virtual void setNumRequests(Node * node,int num);

  /* SPFamily operations */
  // Note: this are different from current VentureLite, since it does not automatically jump
  // from a node to its spmakerNode. (motivation: avoid confusing non-commutativity in particles)
  virtual void registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent);
  virtual void unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent);
  virtual bool containsMadeSPFamily(OutputNode * makerNode, FamilyID id);
  virtual Node * getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id);

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
