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
  assert(makerNode);
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
Node * DetachParticle::getSourceNode(Node * node) { return trace->getSourceNode(node); }
void DetachParticle::clearSourceNode(Node * node) 
{ 
  assert(!sourceNodes.count(node));
  sourceNodes[node] = trace->getSourceNode(node);
  trace->clearSourceNode(node); 
}

void DetachParticle::clearValue(Node * node)
{
  trace->clearValue(node);
}

VentureValue * DetachParticle::getValue(Node * node) { return trace->getValue(node); }

SP * DetachParticle::getSP(Node * node) { return trace->getSP(node); }
VentureSP * DetachParticle::getVSP(Node * node) { return trace->getVSP(node); }
SPAux * DetachParticle::getSPAux(Node * node) { return trace->getSPAux(node); }
SPAux * DetachParticle::getMadeSPAux(Node * makerNode){ return trace->getMadeSPAux(makerNode); }
Args DetachParticle::getArgs(Node * node) { return trace->getArgs(node); }
vector<Node *> DetachParticle::getESRParents(Node * node) { return trace->getESRParents(node); }
  
void DetachParticle::unconstrainChoice(Node * node)
{
  // happens before we register choice, so no need to undo that
  crcs.insert(node);
  trace->unconstrainChoice(node);
}

// During commit, we will iterate over constrained choices, so there we can set
// node->isConstrained = true and node->spOwnsValue = false
void DetachParticle::clearConstrained(Node * node) { trace->clearConstrained(node); }

void DetachParticle::setNodeOwnsValue(Node * node) { trace->setNodeOwnsValue(node); }

Node * DetachParticle::removeLastESREdge(Node * outputNode)
{
  assert(sourceNodes.count(outputNode));
  Node * esrParent = trace->removeLastESREdge(outputNode);
  esrParents[outputNode].push(esrParent);
  children.insert({esrParent,outputNode});
  return esrParent;
}

void DetachParticle::detachMadeSPAux(Node * makerNode)
{
  maybeCloneMadeSPAux(makerNode);
  trace->detachMadeSPAux(makerNode);
}

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
  assert(!values.count(node));
  values[node] = trace->getValue(node);
}

void DetachParticle::prepareLatentDB(SP * sp) { }

LatentDB * DetachParticle::getLatentDB(SP * sp) { return sp->constructLatentDB(); }
void DetachParticle::processDetachedLatentDB(SP * sp, LatentDB * latentDB) { sp->destroyLatentDB(latentDB); }

void DetachParticle::registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values)
{
  spOwnedValues.insert(spOwnedValues.end(),values.begin(),values.end());
}

void DetachParticle::registerSPFamily(Node * makerNode,size_t id,Node * root) {}


void DetachParticle::unregisterRandomChoice(Node * node) 
{ 
  if (!crcs.count(node)) { rcs.insert(node); }
  trace->unregisterRandomChoice(node);
}

void DetachParticle::disconnectLookup(Node * node)
{
  children.insert({node->lookedUpNode,node});
}

void DetachParticle::clearVSPMakerNode(Node * node)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(getValue(node));
  assert(vsp);
  vspMakerNodes[vsp] = vsp->makerNode;
  trace->clearVSPMakerNode(node);
}

