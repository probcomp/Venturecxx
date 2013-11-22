#include "particle.h"
#include "trace.h"
#include "node.h"
#include "value.h"
#include "sp.h"
#include "spaux.h"
#include "flush.h"

// map<Node *, ParticleNode> pnodes;
// map<Node *, vector<Node *> > children;
// map<Node*,SPAux*> spauxs;

// set<Node *> randomChoices;
// set<Node *> constrainedChoices;

// queue<FlushEntry> flushQueue;
// set<Node *> random

// Trace * trace{nullptr};

void DetachParticle::maybeCloneSPAux(Node * node)
{
  Node * makerNode = getVSP(node)->makerNode;
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void DetachParticle::maybeCloneMadeSPAux(Node * makerNode)
{
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}


bool DetachParticle::isReference(Node * node) { return trace->isReference(node); }
void DetachParticle::registerReference(Node * node, Node * lookedUpNode) { assert(false); }
Node * DetachParticle::getSourceNode(Node * node) { assert(false); }
void DetachParticle::setSourceNode(Node * node, Node * sourceNode) { assert(false); }
void DetachParticle::clearSourceNode(Node * node) 
{ 
  assert(!pnodes.count(node));
  pnodes[node] = ParticleNode(trace->getSourceNode(node));
  trace->clearSourceNode(node); 
}

void DetachParticle::setValue(Node * node, VentureValue * value) { assert(false); }
void DetachParticle::clearValue(Node * node)
{
}

VentureValue * DetachParticle::getValue(Node * node) { return trace->getValue(node); }

SP * DetachParticle::getSP(Node * node) { return trace->getSP(node); }
VentureSP * DetachParticle::getVSP(Node * node) { return trace->getVSP(node); }
SPAux * DetachParticle::getSPAux(Node * node) { return trace->getSPAux(node); }
SPAux * DetachParticle::getMadeSPAux(Node * makerNode){ return trace->getMadeSPAux(makerNode); }
Args DetachParticle::getArgs(Node * node) { return trace->getArgs(node); }
vector<Node *> DetachParticle::getESRParents(Node * node) { return trace->getESRParents(node); }
  
void DetachParticle::constrainChoice(Node * node) { assert(false); }

void DetachParticle::unconstrainChoice(Node * node)
{
  // happens before we register choice, so no need to undo that
  crcs.insert(node);
  trace->unconstrainChoice(node);
}

// During commit, we will iterate over constrained choices, so there we can set
// node->isConstrained = true and node->spOwnsValue = false
void DetachParticle::clearConstrained(Node * node) { trace->clearConstrained(node); }
void DetachParticle::setConstrained(Node * node) { assert(false); }

void DetachParticle::setNodeOwnsValue(Node * node) { trace->setNodeOwnsValue(node); }
void DetachParticle::clearNodeOwnsValue(Node * node) { assert(false); }

Node * DetachParticle::removeLastESREdge(Node * outputNode)
{
  Node * esrParent = trace->removeLastESREdge(outputNode);
  ParticleNode & pnode = pnodes[outputNode];
  pnode.esrParents.insert(pnode.esrParents.begin(),esrParent);
  children.insert({esrParent,outputNode});
  return esrParent;
}

void DetachParticle::addESREdge(Node * esrParent,Node * outputNode) { assert(false); }

void DetachParticle::detachMadeSPAux(Node * makerNode)
{
  maybeCloneMadeSPAux(makerNode);
  trace->detachMadeSPAux(makerNode);
}

void DetachParticle::preAbsorb(Node * node) { assert(false); }
void DetachParticle::preApplyPSP(Node * node) { assert(false); }
void DetachParticle::preEvalRequests(Node * requestNode) { assert(false); }
void DetachParticle::preConstrain(Node * node) { assert(false); }


void DetachParticle::preUnabsorb(Node * node) { maybeCloneSPAux(node); }

void DetachParticle::preUnapplyPSP(Node * node) { maybeCloneSPAux(node); }

void DetachParticle::preUnevalRequests(Node * requestNode) { }

void DetachParticle::preUnconstrain(Node * node) { maybeCloneSPAux(node); }

void DetachParticle::extractLatentDB(SP * sp,LatentDB * latentDB) { sp->destroyLatentDB(latentDB); }
void DetachParticle::registerGarbage(SP * sp,VentureValue * value,NodeType nodeType)
{
  flushDeque.push_front(FlushEntry(sp,value,nodeType)); 
}

void DetachParticle::extractValue(Node * node, VentureValue * value)
{
  assert(!pnodes.count(node));
  pnodes[node] = ParticleNode(trace->getValue(node));
}

void DetachParticle::prepareLatentDB(SP * sp) { }

LatentDB * DetachParticle::getLatentDB(SP * sp) { return sp->constructLatentDB(); }
void DetachParticle::processDetachedLatentDB(SP * sp, LatentDB * latentDB) { sp->destroyLatentDB(latentDB); }

void DetachParticle::registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values)
{
  spOwnedValues.insert(spOwnedValues.end(),values.begin(),values.end());
}

void DetachParticle::registerSPFamily(Node * makerNode,size_t id,Node * root) {}


void DetachParticle::registerRandomChoice(Node * node) { assert(false); }
void DetachParticle::unregisterRandomChoice(Node * node) 
{ 
  rcs.insert(node);
  trace->unregisterRandomChoice(node);
}

void DetachParticle::disconnectLookup(Node * node)
{
  children.insert({node->lookedUpNode,node});
}

void DetachParticle::reconnectLookup(Node * node) { assert(false); }
void DetachParticle::connectLookup(Node * node, Node * lookedUpNode) { assert(false); }
