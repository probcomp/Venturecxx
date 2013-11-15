#include "node.h"
#include "value.h"
#include "trace.h"
#include "omegadb.h"
#include "sp.h"
#include "spaux.h"
#include "flush.h"
#include "scaffold.h"
#include "lkernel.h"
#include "sps/csp.h"
#include "sps/mem.h"

#include <iostream>
#include <boost/range/adaptor/reversed.hpp>
#include <tuple>

#include <typeinfo>

using boost::adaptors::reverse;

double Trace::extract(const vector<Node *> & border,
		      Scaffold * scaffold,
		      Particle * rho)
{
  assert(scaffold);

  double weight = 0;

  for (Node * node : reverse(border))
  {
    if (scaffold->isAbsorbing(node))
    { 
      weight += unabsorb(node,scaffold,rho); 
    }
    else
    {
      assert(scaffold->isResampling(node));
      if (node->isObservation()) 
      { 
	weight += unconstrain(node,false);
      }
      weight += extractInternal(node,scaffold,rho);
    }
  }
  
  return make_pair(weight,rho);
}

double Trace::extractParents(Node * node,
			    Scaffold * scaffold,
			    Particle * rho)
{
  assert(scaffold);
  double weight = 0;
  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return extractInternal(node->lookedUpNode,scaffold,rho); }

  if (node->nodeType == NodeType::OUTPUT)
  {
    for (Node * esrParent : reverse(node->esrParents))
    { weight += extractInternal(esrParent,scaffold,rho); }
    weight += extractInternal(node->requestNode,scaffold,rho);
  }
  for (Node * operandNode : reverse(node->operandNodes))
  { weight += extractInternal(operandNode,scaffold,rho); }
  weight += extractInternal(node->operatorNode,scaffold,rho);
  return weight;
}

double Trace::unabsorb(Node * node,
		       Scaffold * scaffold,
		       Particle * rho)
{
  assert(scaffold);
  double weight = 0;
  rho->maybeCloneSPAux(node);
  Args args(node);
  node->sp()->remove(node->value,args);
  weight += node->sp()->logDensity(node->value,args);
  weight += extractParents(node,scaffold,rho);
  return weight;
}

double Trace::unconstrain(Node * node, bool giveOwnershipToSP)
{
  assert(node->isActive);
  if (node->isReference())
  { return unconstrain(node->sourceNode,giveOwnershipToSP); }
  else
  {
    /* Subtle and looks a little crazy. We modify the trace, but we leave the RHO particle in
       a state so that we can copy things in to commit. */
    if (node->sp()->isRandomOutput) 
    { 
      unregisterConstrainedChoice(node);
      registerRandomChoice(node);

      rho->unregisterRandomChoice(node);
      rho->registerConstrainedChoice(node);
    }
    rho->maybeCloneSPAux(node);
    Args args(node);
    node->sp()->removeOutput(node->value,args);
    double logDensity = node->sp()->logDensityOutput(node->value,args);
    node->isConstrained = false;
    node->spOwnsValue = giveOwnershipToSP;
    node->sp()->incorporateOutput(node->value,args);
    return logDensity;
  }
}

double Trace::extractInternal(Node * node,
			     Scaffold * scaffold,
			     Particle * rho)
{
  if (!scaffold) { return 0; }
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    drgNode.regenCount--;
    assert(drgNode.regenCount >= 0);
    if (drgNode.regenCount == 0)
    {
      node->isActive = false;
      if (node->isApplication())
      { 
	weight += unapplyPSP(node,scaffold,rho); 
      }
      else
      {
	rho->registerReference(node,node->lookedUpNode);
      }

      weight += extractParents(node,scaffold,rho);
    }
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += extractInternal(node->sourceNode,scaffold,rho); }
  }
  return weight;
}

void Trace::teardownMadeSP(Node * node, bool isAAA,Particle * rho)
{
  callCounts[{"processMadeSP",true}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(node->value);

  if (vsp->makerNode != node) { return; }

  callCounts[{"processMadeSPfull",true}]++;

  rho->maybeCloneMadeSPAux(node); // even if AAA

  vsp->makerNode = nullptr;

  SP * madeSP = vsp->sp;

  if (!isAAA)
  {
    if (madeSP->hasAux()) 
    { 
      delete node->madeSPAux; 
      node->madeSPAux = nullptr;
    }
  }

  
}


double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold,
			 Particle * rho)
{
  callCounts[{"applyPSP",true}]++;

  assert(node->isValid());
  assert(node->sp()->isValid());


  if (node->nodeType == NodeType::OUTPUT && node->sp()->isESRReference) 
  { 
    rho->registerReference(node,node->esrParents[0]);
    node->sourceNode = nullptr;
    return 0; 
  }
  if (node->nodeType == NodeType::REQUEST && node->sp()->isNullRequest()) { return 0; }

  
  assert(node->value->isValid());

  if (node->nodeType == NodeType::REQUEST) { unevalRequests(node,scaffold,rho); }
  if (node->sp()->isRandom(node->nodeType)) 
  { 
    unregisterRandomChoice(node); 
    rho->registerRandomChoice(node);
  }
  
  if (dynamic_cast<VentureSP*>(node->value))
  { teardownMadeSP(node,scaffold && scaffold->isAAA(node),rho); }

  SP * sp = node->sp();
  double weight = 0;

  rho->maybeCloneSPAux(node);
  Args args(node);
  sp->remove(node->value,args);

  if (scaffold && scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(node->value,args); }

  if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
  { 
    pair<double, LatentDB *> p = node->sp()->detachAllLatents(node->spaux());
    weight += p.first;
  }

  if (node->spOwnsValue) 
  { 
    rho->flushQueue.emplace(node->sp(),node->value,node->nodeType); 
  }

  rho->setValue(node,node->value); 
  node->clearValue();

  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold,
			     Particle * rho)
{
  assert(node->nodeType == NodeType::REQUEST);
  if (!node->value) { return 0; }

  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->value);

  rho->maybeCloneSPAux(node);

  for (HSR * hsr : reverse(requests->hsrs))
  {
    weight += node->sp()->detachLatents(node->spaux(),hsr);
  }

  for (ESR esr : reverse(requests->esrs))
  {
    assert(node->spaux());
    assert(node->spaux()->isValid());
    assert(!node->outputNode->esrParents.empty());
    Node * esrParent = node->outputNode->removeLastESREdge();
    rho->esrParents[node->outputNode].insert(0,spaux->families[esr.id]);

    assert(esrParent);
    assert(esrParent->isValid());

    if (esrParent->numRequests == 0)
    { 
      weight += extractSPFamily(node->vsp(),esr.id,scaffold,rho); 
    }
  }

  return weight;
}

double Trace::extractSPFamily(VentureSP * vsp,
			     size_t id,
			     Scaffold * scaffold,
			     Particle * rho)
{
  assert(vsp);
  assert(vsp->makerNode);
  assert(vsp->makerNode->madeSPAux);

  assert(rho->getMadeSPAux(vsp->makerNode));

  SPAux * spaux = vsp->makerNode->madeSPAux;
  Node * root = spaux->families[id];
  assert(root);
  spaux->families.erase(id);

  spaux->ownedValues.erase(id);
  
  double weight = extractFamily(root,scaffold,rho);
  return weight;
}

double Trace::extractFamily(Node * node,
			   Scaffold * scaffold,
			   Particle * rho)
{
  assert(node);
  double weight = 0;
  
  if (node->nodeType == NodeType::VALUE) 
  { 
    rho->setValue(node,node->getValue());
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    Node * lookedUpNode = node->lookedUpNode;
    rho->registerReference(node,lookedUpNode);
    node->disconnectLookup();
    weight += extractInternal(lookedUpNode,scaffold,rho);
  }
  else
  {
    weight += unapply(node,scaffold,rho);
    for (Node * operandNode : reverse(node->operandNodes))
    { weight += extractFamily(operandNode,scaffold,rho); }
    weight += extractFamily(node->operatorNode,scaffold,rho);
  }
  return weight;
}

double Trace::unapply(Node * node,
		      Scaffold * scaffold,
		      Particle * rho)
{
  double weight = 0;

  weight += unapplyPSP(node,scaffold,rho);
  for (Node * esrParent : reverse(node->esrParents))
  { weight += extractInternal(esrParent,scaffold,rho); }
  weight += unapplyPSP(node->requestNode,scaffold,rho);

  return weight;
}
