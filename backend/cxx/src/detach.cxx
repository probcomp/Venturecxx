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

pair<double, OmegaDB*> Trace::detach(const vector<Node *> & border,
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
      weight += detachInternal(node,scaffold,rho);
    }
  }
  
  return make_pair(weight,rho);
}

double Trace::detachParents(Node * node,
			    Scaffold * scaffold,
			    Particle * rho)
{
  assert(scaffold);
  double weight = 0;
  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return detachInternal(node->lookedUpNode,scaffold,rho); }

  if (node->nodeType == NodeType::OUTPUT)
  {
    for (Node * esrParent : reverse(node->esrParents))
    { weight += detachInternal(esrParent,scaffold,rho); }
    weight += detachInternal(node->requestNode,scaffold,rho);
  }
  for (Node * operandNode : reverse(node->operandNodes))
  { weight += detachInternal(operandNode,scaffold,rho); }
  weight += detachInternal(node->operatorNode,scaffold,rho);
  return weight;
}

double Trace::unabsorb(Node * node,
		       Scaffold * scaffold,
		       Particle * rho)
{
  assert(scaffold);
  double weight = 0;

  //clones if it hasn't been used yet this time slice
  rho->maybeCloneSPAux(node->vsp()->makerNode); 
  node->sp()->remove(node->getValue(),node);
  weight += node->sp()->logDensity(node->getValue(),node);
  weight += detachParents(node,scaffold,rho);
  return weight;
}

double Trace::unconstrain(Node * node, bool giveOwnershipToSP)
{
  assert(node->isActive);
  if (node->isReference())
  { return unconstrain(node->sourceNode,giveOwnershipToSP); }
  else
  {
    if (node->sp()->isRandomOutput) { 
      unregisterConstrainedChoice(node);
      registerRandomChoice(node);
    }
    rho->maybeCloneSPAux(node->vsp()->makerNode); 
    node->sp()->removeOutput(node->getValue(),node);
    double logDensity = node->sp()->logDensityOutput(node->getValue(),node);
    node->isConstrained = false;
    node->spOwnsValue = giveOwnershipToSP;
    node->sp()->incorporateOutput(node->getValue(),node);
    return logDensity;
  }
}

double Trace::detachInternal(Node * node,
			     Scaffold * scaffold,
			     Particle * rho)
{
  if (!scaffold) { return 0; }
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    drgNode.regenCount--;
    if (drgNode.regenCount < 0)
    {
      cout << "\n\n\n\n\n---RegenCount < 0! (" << node << ")---\n\n\n" << endl;
      scaffold->show();
    }

    assert(drgNode.regenCount >= 0);
    if (drgNode.regenCount == 0)
    {
      node->isActive = false;
      if (node->isApplication())
      { 
	weight += unapplyPSP(node,scaffold,rho); 
      }

      weight += detachParents(node,scaffold,rho);
    }
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += detachInternal(node->sourceNode,scaffold,rho); }
  }
  return weight;
}

void Trace::teardownMadeSP(Node * node, bool isAAA,Particle * rho)
{
  callCounts[{"processMadeSP",true}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(node->getValue());

  if (vsp->makerNode != node) { return; }

  // called even if AAA (subtle)
  rho->maybeCloneSPAux(vsp->makerNode);

  callCounts[{"processMadeSPfull",true}]++;

  vsp->makerNode = nullptr;

  SP * madeSP = vsp->sp;

  if (!isAAA)
  {
    if (madeSP->hasAEKernel) { unregisterAEKernel(vsp); }
    if (madeSP->hasAux()) 
    { 
//      rho->flushQueue.emplace(madeSP,node->madeSPAux); 
      delete node->madeSPAux; 
      node->madeSPAux = nullptr;
    }
  }
}


double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold,
			 Particle * rho)
{
  DPRINT("unapplyPSP: ", node->address.toString());
  callCounts[{"applyPSP",true}]++;

  assert(node->isValid());
  assert(node->sp()->isValid());



  if (node->nodeType == NodeType::OUTPUT && node->sp()->isESRReference) 
  { 
    node->sourceNode = nullptr;
    return 0; 
  }
  if (node->nodeType == NodeType::REQUEST && node->sp()->isNullRequest()) { return 0; }

  
  assert(node->getValue()->isValid());

  if (node->nodeType == NodeType::REQUEST) { unevalRequests(node,scaffold,rho); }
  if (node->sp()->isRandom(node->nodeType)) { 
    unregisterRandomChoice(node); 
  }
  
  if (dynamic_cast<VentureSP*>(node->getValue()))
  { teardownMadeSP(node,scaffold && scaffold->isAAA(node),rho); }

  SP * sp = node->sp();
  double weight = 0;

  rho->maybeCloneSPAux(node->vsp()->makerNode);

  sp->remove(node->getValue(),node);

  if (scaffold && scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(node->getValue(),node,nullptr); }

  if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
  { 
    pair<double, LatentDB *> p = node->sp()->detachAllLatents(node->spaux());
    weight += p.first;
    assert(!rho->latentDBs.count(node->sp()));
    rho->latentDBs.insert({node->sp(),p.second});
  }



  if (node->spOwnsValue) 
  { 

    rho->flushQueue.emplace(node->sp(),node->getValue(),node->nodeType); 
  }

  if (scaffold && scaffold->isResampling(node))
  { rho->drgDB[node] = node->getValue();  node->clearValue(); }


  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold,
			     Particle * rho)
{
  assert(node->nodeType == NodeType::REQUEST);
  if (!node->getValue()) { return 0; }

  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  rho->maybeCloneSPAux(node->vsp()->makerNode);

  if (!requests->hsrs.empty() && !rho->latentDBs.count(node->sp()))
  { rho->latentDBs[node->sp()] = node->sp()->constructLatentDB(); }

  for (HSR * hsr : reverse(requests->hsrs))
  {
    LatentDB * latentDB = rho->latentDBs[node->sp()];
    weight += node->sp()->detachLatents(node->spaux(),hsr,latentDB);
  }

  for (ESR esr : reverse(requests->esrs))
  {
    assert(node->spaux());
    assert(node->spaux()->isValid());
    assert(!node->outputNode->esrParents.empty());
    Node * esrParent = node->outputNode->removeLastESREdge();
    assert(esrParent);
    assert(esrParent->isValid());

    if (esrParent->numRequests == 0)
    { 
      weight += detachSPFamily(node->vsp(),esr.id,scaffold,rho); 
    }
  }

  return weight;
}

double Trace::detachSPFamily(VentureSP * vsp,
			     size_t id,
			     Scaffold * scaffold,
			     Particle * rho)
{
  assert(vsp);
  assert(vsp->makerNode);
  assert(vsp->makerNode->madeSPAux);
  SPAux * spaux = vsp->makerNode->madeSPAux;
  Node * root = spaux->families[id];
  assert(root);
  spaux->families.erase(id);

  if (!spaux->ownedValues.empty())
  {
    rho->spOwnedValues[make_pair(vsp->makerNode,id)] = spaux->ownedValues[id];
  }

  spaux->ownedValues.erase(id);

  rho->spFamilyDBs[{vsp->makerNode,id}] = root;
  
  double weight = detachFamily(root,scaffold,rho);
  return weight;
}

/* Does not erase from ventureFamilies */
double Trace::detachVentureFamily(Node * root,Particle * rho)
{
  assert(root);
  return detachFamily(root,nullptr,rho);
}

double Trace::detachFamily(Node * node,
			   Scaffold * scaffold,
			   Particle * rho)
{
  assert(node);
  DPRINT("uneval: ", node->address.toString());
  double weight = 0;
  
  if (node->nodeType == NodeType::VALUE) 
  { 
    // do nothing! (finally!)
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    Node * lookedUpNode = node->lookedUpNode;
    node->disconnectLookup();
    weight += detachInternal(lookedUpNode,scaffold,rho);
  }
  else
  {
    weight += unapply(node,scaffold,rho);
    for (Node * operandNode : reverse(node->operandNodes))
    { weight += detachFamily(operandNode,scaffold,rho); }
    weight += detachFamily(node->operatorNode,scaffold,rho);
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
  { weight += detachInternal(esrParent,scaffold,rho); }
  weight += unapplyPSP(node->requestNode,scaffold,rho);

  return weight;
}
