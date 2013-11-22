#include "particle.h"
#include "trace.h"
#include "node.h"
#include "value.h"
#include "sp.h"
#include "spaux.h"
#include "flush.h"

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


void DetachParticle::clearSourceNode(Node * node) 
{ 
  assert(!sourceNodes.count(node));
  sourceNodes[node] = trace->getSourceNode(node);
  trace->clearSourceNode(node); 
}

void DetachParticle::unconstrainChoice(Node * node)
{
  // happens before we register choice, so no need to undo that
  crcs.insert(node);
  trace->unconstrainChoice(node);
}

// During commit, we will iterate over constrained choices, so there we can set
// node->isConstrained = true and node->spOwnsValue = false

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

void DetachParticle::preUnconstrain(Node * node) { maybeCloneSPAux(node); }

void DetachParticle::prepareLatentDB(SP * sp) {  }
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
  trace->disconnectLookup(node);
}

void DetachParticle::clearVSPMakerNode(Node * node)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(getValue(node));
  assert(vsp);
  vspMakerNodes[vsp] = vsp->makerNode;
  trace->clearVSPMakerNode(node);
}

