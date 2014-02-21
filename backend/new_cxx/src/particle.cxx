#include "particle.h"
#include "concrete_trace.h"

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
  void Particle::unregisterUnconstrainedChoice(Node * node) 
  { 
    assert(unconstrainedChoices.contains(node));
    unconstrainedChoices = unconstrainedChoices.remove(node);
    unregisterUnconstrainedChoiceInScope(VentureValuePtr(new VentureSymbol("default")),
					 VentureValuePtr(new VentureNode(node)),
					 node);
  }

  void Particle::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
  { 
    assert(false); // TODO
  }

  /* These will never be called */

  /* Regen mutations */
  void Particle::addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) { assert(false); }
  void Particle::reconnectLookup(LookupNode * lookupNode) { assert(false); }
  void Particle::incNumRequests(RootOfFamily root) 
  {
    assert(false); // TODO handle LAMBDA
    // if (!numRequests.contains(node)) { numRequests = numRequests.insert(node,baseTrace->getNumRequests(node)); }
    // numRequests = numRequests.adjust(node,lambda nr: nr + 1);
  }
  void Particle::incRegenCount(shared_ptr<Scaffold> scaffold,Node * node) 
  {
    assert(false); // TODO handle LAMBDA
    // if (!regenCounts.contains(node)) { regenCounts = regenCounts.insert(node,0); }
    // regenCounts = regenCounts.adjust(node,lambda rc: rc + 1);
  }

  void Particle::addChild(Node * node, Node * child) 
  { 
    assert(false); // TODO handle LAMBDA
    // if (!newChildren.contains(node)) { newChildren = newChildren.insert(node,PSet<Node*>()); }
    // newChildren = newChildren.adjust(node, lambda children: children.insert(child));
  }


  /* Primitive getters */
  VentureValuePtr Particle::getValue(Node * node) 
  { 
    if (values.contains(node)) { return values.lookup(node); }
    else { return baseTrace->getValue(node); }
  }

shared_ptr<SP> Particle::getMadeSP(Node * makerNode)
  {
    if (madeSPs.contains(makerNode)) { return madeSPs.lookup(makerNode); }
    else { return baseTrace->getMadeSP(makerNode); }
  }

shared_ptr<SPAux> Particle::getMadeSPAux(Node * makerNode)
  {
    if (!madeSPAuxs.count(makerNode))
    {
      if (baseTrace->getMadeSPAux(makerNode))
      {
	madeSPAuxs[makerNode] = baseTrace->getMadeSPAux(makerNode)->copy();
      }
      else { return shared_ptr<SPAux>(); }
    }
    return madeSPAuxs[makerNode];
  }


  vector<RootOfFamily> Particle::getESRParents(Node * node) 
  {
    if (esrRoots.contains(node)) { return esrRoots.lookup(node); }
    else { return baseTrace->getESRParents(node); }
  }

  int Particle::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) 
  { 
    assert(baseTrace->getRegenCount(scaffold,node) == 0);
    if (regenCounts.contains(node)) { return regenCounts.lookup(node); }
    else { return baseTrace->getRegenCount(scaffold,node); }
  }

  VentureValuePtr Particle::getObservedValue(Node * node) { assert(false); }

  bool Particle::isMakerNode(Node * node) { assert(false); }
  bool Particle::isConstrained(Node * node) { assert(false); }
  bool Particle::isObservation(Node * node) { assert(false); }

  /* Primitive setters */
  void Particle::setValue(Node * node, VentureValuePtr value) 
  { 
    assert(!baseTrace->getValue(node)); // TODO might not work
    values = values.insert(node,value);
  }

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



/* The following should never be called on particles */


  RootOfFamily Particle::popLastESRParent(OutputNode * outputNode) { assert(false); throw "should never be called"; }
  void Particle::disconnectLookup(LookupNode * lookupNode) { assert(false); throw "should never be called"; }
  void Particle::decNumRequests(RootOfFamily root) { assert(false); throw "should never be called"; }
  void Particle::decRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); throw "should never be called"; }
  void Particle::removeChild(Node * node, Node * child) { assert(false); throw "should never be called"; }
  void Particle::unregisterAEKernel(Node * node) { assert(false); throw "should never be called"; }

  void Particle::unregisterConstrainedChoice(Node * node) { assert(false); throw "should never be called"; }
set<Node*> Particle::getChildren(Node * node) { assert(false); throw "should never be called"; }
  int Particle::getNumRequests(RootOfFamily root) { assert(false); throw "should never be called"; }
