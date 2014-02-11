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
  /** AE (Arbitrary Ergodic) kernels repropose random choices within an sp that 
      have no effect on the trace. This optimizes some cases that otherwise could
      be handled by AAA.
   */
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
  virtual pair<RequestNode*,OutputNode*> createApplicationNodes(
                Node *operatorNode,
								const vector<Node*>& operandNodes,
								shared_ptr<VentureEnvironment>& env);

  /* Regen mutations */
  virtual void addESREdge(Node *esrParent,OutputNode * outputNode) =0;
  virtual void reconnectLookup(LookupNode * lookupNode) =0;
  virtual void incNumRequests(Node * node) =0;
  virtual void addChild(Node * node, Node * child) =0;

  /* Detach mutations */  
  virtual Node * popLastESRParent(OutputNode * outputNode) =0;
  virtual void disconnectLookup(LookupNode * lookupNode) =0;
  virtual void decNumRequests(Node * node) =0;
  virtual def removeChild(Node * node, Node * child) =0;

  /* Primitive getters */
  virtual VentureValuePtr getValue(Node * node) =0;
  virtual SPRecord getMadeSPRecord(OutputNode * makerNode) =0;
  virtual vector<Node*> getESRParents(Node * node) =0;
  virtual set<Node*> getChildren(Node * node) =0;
  virtual int getNumRequests(Node * node) =0;
  virtual int getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) =0;
  virtual VentureValuePtr getObservedValue(Node * node) =0;

  virtual bool isConstrained(Node * node) =0;
  virtual bool isObservation(Node * node) =0;

  /* Derived getters (just for convenience)*/
  virtual VentureValuePtr getGroundValue(Node * node);
  virtual Node * getSPMakerNode(Node * node);
  virtual shared_ptr<SPRef> getSPRef(Node * node);
  virtual shared_ptr<VentureSP> getMadeSP(Node * node);
  virtual shared_ptr<SPFamilies> getMadeSPFamilies(Node * node);
  virtual shared_ptr<SPAux> getMadeSPAux(Node * node);
  virtual shared_ptr<PSP> getMadePSP(Node * node);
  virtual vector<Node*> getParents(Node * node);

  /* Primitive setters */
  virtual void setValue(Node * node, VentureValuePtr value) =0;
  virtual void clearValue(Node * node) =0;

  virtual void createSPRecord(OutputNode * makerNode) =0; // No analogue in VentureLite

  virtual void initMadeSPFamilies(Node * node) =0;
  virtual void clearMadeSPFamilies(Node * node) =0;

  virtual void setMadeSP(Node * node,shared_ptr<VentureSP> sp) =0;
  virtual void setMadeSPAux(Node * node,shared_ptr<SPAux> spaux) =0;

  virtual void setChildren(Node * node,set<Node*> children) =0;
  virtual void setESRParents(Node * node,const vector<Node*> & esrParents) =0;

  virtual void setNumRequests(Node * node,int num) =0;

  /* SPFamily operations */
  // Note: this are different from current VentureLite, since it does not automatically jump
  // from a node to its spmakerNode. (motivation: avoid confusing non-commutativity in particles)
  virtual void registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent) =0;
  virtual void unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent) =0;
  virtual bool containsMadeSPFamily(OutputNode * makerNode, FamilyID id) =0;
  virtual Node * getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id) =0;

};


#endif
