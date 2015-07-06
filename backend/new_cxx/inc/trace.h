// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#ifndef TRACE_H
#define TRACE_H

#include "types.h"
#include "sprecord.h"
#include "smap.h"
#include "node.h"
#include "scaffold.h"
#include "psp.h"
#include <ctime>

#include <gsl/gsl_rng.h>

struct Node;
struct SPRef;
struct LKernel;

struct Trace 
{
  /* Registering metadata */
  /** AE (Arbitrary Ergodic) kernels repropose random choices within an sp that 
      have no effect on the trace. This optimizes some cases that otherwise could
      be handled by AAA.
   */
  virtual void registerAEKernel(Node * node) =0;
  virtual void registerUnconstrainedChoice(Node * node) =0;
  virtual void registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void registerConstrainedChoice(Node * node) =0;

  /* Unregistering metadata */
  virtual void unregisterAEKernel(Node * node) =0;
  virtual void unregisterUnconstrainedChoice(Node * node) =0;
  virtual void unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) =0;
  virtual void unregisterConstrainedChoice(Node * node) =0;

  /* Creating nodes */
  virtual ConstantNode * createConstantNode(VentureValuePtr);
  virtual LookupNode * createLookupNode(Node * sourceNode,VentureValuePtr exp);
  virtual pair<RequestNode*,OutputNode*> createApplicationNodes(Node * operatorNode,
								const vector<Node*> & operandNodes,
								const boost::shared_ptr<VentureEnvironment> & env,
								VentureValuePtr exp);

  /* Regen mutations */
  virtual void addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) =0;
  virtual void reconnectLookup(LookupNode * lookupNode) =0;
  virtual void incNumRequests(RootOfFamily root) =0;
  virtual void incRegenCount(boost::shared_ptr<Scaffold> scaffold,Node * node) =0;

  virtual bool hasLKernel(boost::shared_ptr<Scaffold> scaffold, Node * node) =0;
  virtual void registerLKernel(boost::shared_ptr<Scaffold> scaffold,Node * node,boost::shared_ptr<LKernel> lkernel) =0;
  virtual boost::shared_ptr<LKernel> getLKernel(boost::shared_ptr<Scaffold> scaffold, Node * node) =0;
  virtual void addChild(Node * node, Node * child) =0;

  /* Detach mutations */  
  virtual RootOfFamily popLastESRParent(OutputNode * outputNode) =0;
  virtual void disconnectLookup(LookupNode * lookupNode) =0;
  virtual void decNumRequests(RootOfFamily root) =0;
  virtual void decRegenCount(boost::shared_ptr<Scaffold> scaffold,Node * node) =0;
  virtual void removeChild(Node * node, Node * child) =0;

  /* Primitive getters */
  virtual VentureValuePtr getValue(Node * node) =0;
  virtual vector<RootOfFamily> getESRParents(Node * node) =0;
  virtual set<Node*> getChildren(Node * node) =0;
  virtual int getNumRequests(RootOfFamily root) =0;
  virtual int getRegenCount(boost::shared_ptr<Scaffold> scaffold,Node * node) =0;

  virtual boost::shared_ptr<SP> getMadeSP(Node * makerNode) =0;
  virtual boost::shared_ptr<SPAux> getMadeSPAux(Node * node) =0;

  virtual VentureValuePtr getObservedValue(Node * node) =0;

  virtual bool isMakerNode(Node * node) =0;
  virtual bool isConstrained(Node * node) =0;
  virtual bool isObservation(Node * node) =0;

  /* Derived getters (just for convenience)*/
  virtual VentureValuePtr getGroundValue(Node * node);
  virtual Node * getOperatorSPMakerNode(ApplicationNode * node);
  virtual vector<Node*> getParents(Node * node);
  virtual boost::shared_ptr<Args> getArgs(ApplicationNode * node);
  virtual boost::shared_ptr<PSP> getPSP(ApplicationNode * node);

  /* Primitive setters */
  virtual void setValue(Node * node, VentureValuePtr value) =0;
  virtual void clearValue(Node * node) =0;


  virtual void setMadeSPRecord(Node * makerNode,boost::shared_ptr<VentureSPRecord> spRecord) =0;
  virtual void destroyMadeSPRecord(Node * makerNode) =0;

  virtual void setMadeSP(Node * makerNode,boost::shared_ptr<SP> sp) =0;
  virtual void setMadeSPAux(Node * makerNode,boost::shared_ptr<SPAux> spaux) =0;

  virtual void setChildren(Node * node,set<Node*> children) =0;
  virtual void setESRParents(Node * node,const vector<RootOfFamily> & esrRoots) =0;

  virtual void setNumRequests(RootOfFamily node,int num) =0;

  /* SPFamily operations */
  // Note: this are different from current VentureLite, since it does not automatically jump
  // from a node to its spmakerNode. (motivation: avoid confusing non-commutativity in particles)
  virtual void registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot) =0;
  virtual void unregisterMadeSPFamily(Node * makerNode,FamilyID id) =0;

  virtual bool containsMadeSPFamily(Node * makerNode, FamilyID id) =0;
  virtual RootOfFamily getMadeSPFamilyRoot(Node * makerNode, FamilyID id) =0;

  virtual OutputNode * getConstrainableNode(Node * node);
  virtual Node * getOutermostNonReferenceNode(Node * node);

  virtual double logDensityOfBlock(ScopeID scope);
  virtual int numBlocksInScope(ScopeID scope) =0;


  virtual bool hasAAAMadeSPAux(OutputNode * makerNode) =0;
  virtual void registerAAAMadeSPAux(OutputNode * makerNode,boost::shared_ptr<SPAux> spAux) =0;
  virtual void discardAAAMadeSPAux(OutputNode * makerNode) =0;
  virtual boost::shared_ptr<SPAux> getAAAMadeSPAux(OutputNode * makerNode) =0;

  virtual gsl_rng * getRNG() =0;
};


#endif
