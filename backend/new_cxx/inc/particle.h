// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#ifndef PARTICLE_H
#define PARTICLE_H

#include "types.h"
#include "trace.h"
#include "smap.h"
#include "value.h"

#include "rng.h"
#include "pset.hpp"
#include "pmap.hpp"

using persistent::PMap;
using persistent::PSet;

struct Particle : Trace
{
  Particle(ConcreteTrace * outerTrace, unsigned long seed);
  Particle(const shared_ptr<Particle> & outerParticle, unsigned long seed);

/* Methods */

  /* Registering metadata */
  void registerAEKernel(Node * node);
  void registerUnconstrainedChoice(Node * node);
  void registerUnconstrainedChoiceInScope(
      const ScopeID & scope, const BlockID & block, Node * node);
  void registerConstrainedChoice(Node * node);

  /* Unregistering metadata */
  void unregisterAEKernel(Node * node);
  void unregisterUnconstrainedChoice(Node * node);
  void unregisterUnconstrainedChoiceInScope(
      const ScopeID & scope, const BlockID & block, Node * node);
  void unregisterConstrainedChoice(Node * node);

  /* Regen mutations */
  void addESREdge(const RootOfFamily & esrRoot, OutputNode * outputNode);
  void reconnectLookup(LookupNode * lookupNode);
  void incNumRequests(const RootOfFamily & root);
  void incRegenCount(
      const shared_ptr<Scaffold> & scaffold, Node * node);

  bool hasLKernel(const shared_ptr<Scaffold> & scaffold, Node * node);
  void registerLKernel(
      const shared_ptr<Scaffold> & scaffold,
      Node * node,
      const shared_ptr<LKernel> & lkernel);
  shared_ptr<LKernel> getLKernel(
      const shared_ptr<Scaffold> & scaffold, Node * node);
  void addChild(Node * node, Node * child);

  /* Detach mutations */
  RootOfFamily popLastESRParent(OutputNode * outputNode);
  void disconnectLookup(LookupNode * lookupNode);
  void decNumRequests(const RootOfFamily & root);
  void decRegenCount(const shared_ptr<Scaffold> & scaffold, Node * node);
  void removeChild(Node * node, Node * child);

  /* Primitive getters */
  gsl_rng * getRNG();
  const VentureValuePtr & getValue(Node * node);
  shared_ptr<SP> getMadeSP(Node * makerNode);
  shared_ptr<SPAux> getMadeSPAux(Node * makerNode);
  vector<RootOfFamily> getESRParents(Node * node);
  set<Node*> getChildren(Node * node);
  int getNumRequests(const RootOfFamily & root);
  int getRegenCount(const shared_ptr<Scaffold> & scaffold, Node * node);

  VentureValuePtr getObservedValue(Node * node);

  bool isMakerNode(Node * node);
  bool isConstrained(Node * node);
  bool isObservation(Node * node);

  /* Primitive setters */
  void setValue(Node * node, const VentureValuePtr & value);
  void clearValue(Node * node);


  void setMadeSPRecord(
      Node * makerNode, const shared_ptr<VentureSPRecord> & spRecord);
  void destroyMadeSPRecord(Node * makerNode);

  void setMadeSP(Node * makerNode, const shared_ptr<SP> & sp);
  void setMadeSPAux(Node * makerNode, const shared_ptr<SPAux> & spaux);

  void setChildren(Node * node, const set<Node*> & children);
  void setESRParents(Node * node, const vector<RootOfFamily> & esrRoots);

  void setNumRequests(const RootOfFamily & node, int num);

  /* SPFamily operations */
  void registerMadeSPFamily(
      Node * makerNode, const FamilyID & id, const RootOfFamily & esrRoot);
  void unregisterMadeSPFamily(Node * makerNode, const FamilyID & id);

  bool containsMadeSPFamily(Node * makerNode, const FamilyID & id);
  RootOfFamily getMadeSPFamilyRoot(Node * makerNode, const FamilyID & id);

  /* Inference (computing reverse weight) */
  int numBlocksInScope(const ScopeID & scope);

  // "self-explanatory" -Dan Selsam, 2014
  // Commits this particle's data to the concrete trace.
  void commit();

  bool hasAAAMadeSPAux(OutputNode * makerNode);
  void discardAAAMadeSPAux(OutputNode * makerNode);
  void registerAAAMadeSPAux(
      OutputNode * makerNode, const shared_ptr<SPAux> & spAux);
  shared_ptr<SPAux> getAAAMadeSPAux(OutputNode * makerNode);

/* END methods */












/* Members */

  ConcreteTrace * baseTrace;

  /* Persistent data structures, with non-persistent analogs in ConcreteTrace */
  PSet<Node*> unconstrainedChoices;
  PSet<Node*> constrainedChoices;
  PSet<Node*> arbitraryErgodicKernels;

  PMap<DirectiveID, RootOfFamily, VentureValuePtrsLess> families;

  PMap<ScopeID, PMap<BlockID, PSet<Node*>, VentureValuePtrsLess>, VentureValuePtrsLess> scopes;

  PMap<Node*, vector<RootOfFamily> > esrRoots;
  PMap<RootOfFamily, int> numRequests;

  PMap<Node*, VentureValuePtr> values;
  PMap<Node*, shared_ptr<SP> > madeSPs;

  /* persistent, not stored in concrete trace */
  PMap<Node*, int> regenCounts;
  PMap<Node*, shared_ptr<LKernel> > lkernels;

  /* persistent additions */
  PMap<Node*, PMap<FamilyID, RootOfFamily, VentureValuePtrsLess> > newMadeSPFamilies;
  PMap<Node*, PSet<Node*> > newChildren;

  /* Persistent subtractions */
  PSet<OutputNode*> discardedAAAMakerNodes;

  /* Non-persistent */
  map<Node*, shared_ptr<SPAux> > madeSPAuxs;

  /* (optional) rng override */
  shared_ptr<RNGbox> rng;
};



#endif
