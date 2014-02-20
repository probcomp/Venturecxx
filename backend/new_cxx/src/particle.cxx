#include "particle.h"

Particle::Particle(ConcreteTrace * outerTrace): baseTrace(outerTrace) {  }
  Particle::Particle(Particle * outerParticle) { assert(false); }

/* Methods */

  /* Registering metadata */
  void Particle::registerAEKernel(Node * node) 
  {
    arbitraryErgodicKernels = arbitraryErgodicKernels.insert(node);
  }

  void Particle::registerUnconstrainedChoice(Node * node) 
  { 
    unconstrainedChoices = unconstrainedChoices.insert(node);
    registerUnconstrainedChoiceInScope(VentureValuePtr(new VentureSymbol("default")),
				       VentureValuePtr(new VentureNode(node)),
				       node);
  }

  void Particle::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
  { 
    assert(false); // no lambda yet
    // assert(block);
    // if (!scopes.contains(scope)) { scopes = scopes.insert(scope,PMap<ScopeID,PMap<BlockID,PSet<Node*> > >()); }
    // if (!scopes.lookup(scope).contains(block)) { scopes = scopes.adjust(scope,
    // 									lambda blocks: blocks.insert(block,PSet<Node*>())); }
    // scopes = scopes.adjust(scope,lambda blocks: blocks.adjust(block,lambda pnodes: pnodes.insert(node)));
  }

  void Particle::registerConstrainedChoice(Node * node) 
  { 
    constrainedChoices = constrainedChoices.insert(node);
    unregisterUnconstrainedChoice(node);
  }


  /* Unregistering metadata */
  void Particle::unregisterAEKernel(Node * node) { assert(false); }
  void Particle::unregisterUnconstrainedChoice(Node * node) 
  { 
    assert(unconstrainedChoices.contains(node));
    unconstrainedChoices = unconstrainedChoices.remove(node);
    unregisterUnconstrainedChoiceInScope(VentureValuePtr(new VentureSymbol("default")),
					 VentureValuePtr(new VentureNode(node)),
					 node);
  }

  void Particle::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) { assert(false); }
  void Particle::unregisterConstrainedChoice(Node * node) { assert(false); }

  /* Regen mutations */
  void Particle::addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) { assert(false); }
  void Particle::reconnectLookup(LookupNode * lookupNode) { assert(false); }
  void Particle::incNumRequests(RootOfFamily root) { assert(false); }
  void Particle::incRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); }
  void Particle::addChild(Node * node, Node * child) { assert(false); }

  /* Detach mutations */  
  RootOfFamily Particle::popLastESRParent(OutputNode * outputNode) { assert(false); }
  void Particle::disconnectLookup(LookupNode * lookupNode) { assert(false); }
  void Particle::decNumRequests(RootOfFamily root) { assert(false); }
  void Particle::decRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); }
  void Particle::removeChild(Node * node, Node * child) { assert(false); }

  /* Primitive getters */
  VentureValuePtr Particle::getValue(Node * node) { assert(false); }
  shared_ptr<VentureSPRecord> Particle::getMadeSPRecord(Node * makerNode) { assert(false); }
  vector<RootOfFamily> Particle::getESRParents(Node * node) { assert(false); }
  set<Node*> Particle::getChildren(Node * node) { assert(false); }
  int Particle::getNumRequests(RootOfFamily root) { assert(false); }
  int Particle::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); }

  VentureValuePtr Particle::getObservedValue(Node * node) { assert(false); }

  bool Particle::isMakerNode(Node * node) { assert(false); }
  bool Particle::isConstrained(Node * node) { assert(false); }
  bool Particle::isObservation(Node * node) { assert(false); }

  /* Primitive setters */
  void Particle::setValue(Node * node, VentureValuePtr value) { assert(false); }
  void Particle::clearValue(Node * node) { assert(false); }


  void Particle::observeNode(Node * node,VentureValuePtr value) { assert(false); }

  void Particle::setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord) { assert(false); }
  void Particle::destroyMadeSPRecord(Node * makerNode) { assert(false); }

  void Particle::setMadeSP(Node * makerNode,shared_ptr<SP> sp) { assert(false); }
  void Particle::setMadeSPAux(Node * makerNode,shared_ptr<SPAux> spaux) { assert(false); }

  void Particle::setChildren(Node * node,set<Node*> children) { assert(false); }
  void Particle::setESRParents(Node * node,const vector<RootOfFamily> & esrRoots) { assert(false); }

  void Particle::setNumRequests(Node * node,int num) { assert(false); }

  /* SPFamily operations */
  void Particle::registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot) { assert(false); }
  void Particle::unregisterMadeSPFamily(Node * makerNode,FamilyID id) { assert(false); }

  bool Particle::containsMadeSPFamily(Node * makerNode, FamilyID id) { assert(false); }
  RootOfFamily Particle::getMadeSPFamilyRoot(Node * makerNode, FamilyID id) { assert(false); }

  /* Inference (computing reverse weight) */
  double Particle::logDensityOfBlock(ScopeID scope) { assert(false); }
  int Particle::numBlocksInScope(ScopeID scope) { assert(false); }
