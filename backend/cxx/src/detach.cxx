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
					 Scaffold * scaffold)
{
  assert(scaffold);

  double weight = 0;
  OmegaDB * omegaDB = new OmegaDB;

  for (Node * node : reverse(border))
  {
    if (scaffold->isAbsorbing(node))
    { 
      weight += unabsorb(node,scaffold,omegaDB); 
    }
    else
    {
      assert(scaffold->isResampling(node));
      if (node->isObservation()) 
      { 
	weight += unconstrain(node,false);
      }
      weight += detachInternal(node,scaffold,omegaDB);
    }
  }
  
  return make_pair(weight,omegaDB);
}

double Trace::detachParents(Node * node,
			    Scaffold * scaffold,
			    OmegaDB * omegaDB)
{
  assert(scaffold);
  double weight = 0;
  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return detachInternal(node->lookedUpNode,scaffold,omegaDB); }

  if (node->nodeType == NodeType::OUTPUT)
  {
    for (Node * esrParent : reverse(node->esrParents))
    { weight += detachInternal(esrParent,scaffold,omegaDB); }
    weight += detachInternal(node->requestNode,scaffold,omegaDB);
  }
  for (Node * operandNode : reverse(node->operandNodes))
  { weight += detachInternal(operandNode,scaffold,omegaDB); }
  weight += detachInternal(node->operatorNode,scaffold,omegaDB);
  return weight;
}

double Trace::unabsorb(Node * node,
		       Scaffold * scaffold,
		       OmegaDB * omegaDB)
{
  assert(scaffold);
  double weight = 0;
  node->sp()->remove(node->getValue(),node);
  weight += node->sp()->logDensity(node->getValue(),node);
  weight += detachParents(node,scaffold,omegaDB);
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
			     OmegaDB * omegaDB)
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
	weight += unapplyPSP(node,scaffold,omegaDB); 
      }

      weight += detachParents(node,scaffold,omegaDB);
    }
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += detachInternal(node->sourceNode,scaffold,omegaDB); }
  }
  return weight;
}

void Trace::teardownMadeSP(Node * node, bool isAAA,OmegaDB * omegaDB)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(node->getValue());

  if (vsp->makerNode != node) { return; }
  vsp->makerNode = nullptr;

  SP * madeSP = vsp->sp;

  if (!isAAA)
  {
    if (madeSP->hasAEKernel) { unregisterAEKernel(vsp); }
    if (madeSP->hasAux()) 
    { 
      omegaDB->flushQueue.emplace(madeSP,node->madeSPAux); 
      node->madeSPAux = nullptr;
    }
  }
}


double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold,
			 OmegaDB * omegaDB)
{
  DPRINT("unapplyPSP: ", node->address.toString());


  if (node->nodeType == NodeType::OUTPUT && node->sp()->isESRReference) 
  { 
    node->sourceNode = nullptr;
    return 0; 
  }
  if (node->nodeType == NodeType::REQUEST && node->sp()->isNullRequest()) { return 0; }

  if (node->nodeType == NodeType::REQUEST) { unevalRequests(node,scaffold,omegaDB); }
  if (node->sp()->isRandom(node->nodeType)) { 
    unregisterRandomChoice(node); 
  }
  
  if (dynamic_cast<VentureSP*>(node->getValue()))
  { teardownMadeSP(node,scaffold && scaffold->isAAA(node),omegaDB); }

  SP * sp = node->sp();
  double weight = 0;

  sp->remove(node->getValue(),node);

  if (scaffold && scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(node->getValue(),node,nullptr); }

  if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
  { 
    pair<double, LatentDB *> p = node->sp()->detachAllLatents(node->spaux());
    weight += p.first;
    assert(!omegaDB->latentDBs.count(node->sp()));
    omegaDB->latentDBs.insert({node->sp(),p.second});
  }


  if (node->spOwnsValue) 
  { 

    omegaDB->flushQueue.emplace(node->sp(),node->getValue(),node->nodeType); 
  }

  if (scaffold && scaffold->isResampling(node))
  { omegaDB->drgDB[node] = node->getValue();  node->clearValue(); }


  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold,
			     OmegaDB * omegaDB)
{
  assert(node->nodeType == NodeType::REQUEST);
  if (!node->getValue()) { return 0; }

  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  if (!requests->hsrs.empty() && !omegaDB->latentDBs.count(node->sp()))
  { omegaDB->latentDBs[node->sp()] = node->sp()->constructLatentDB(); }

  for (HSR * hsr : reverse(requests->hsrs))
  {
    LatentDB * latentDB = omegaDB->latentDBs[node->sp()];
    weight += node->sp()->detachLatents(node->spaux(),hsr,latentDB);
  }

  for (ESR esr : reverse(requests->esrs))
  {
    assert(node->spaux());
//    assert(!node->outputNode->esrParents.empty());
    Node * esrParent = node->outputNode->removeLastESREdge();
    assert(esrParent);
    if (esrParent->numRequests == 0)
    { 
      weight += detachSPFamily(node->vsp(),esr.id,scaffold,omegaDB); 
    }
  }

  return weight;
}

double Trace::detachSPFamily(VentureSP * vsp,
			     size_t id,
			     Scaffold * scaffold,
			     OmegaDB * omegaDB)
{
  assert(vsp);
  assert(vsp->makerNode);
  assert(vsp->makerNode->madeSPAux);
  SPAux * spaux = vsp->makerNode->madeSPAux;
  Node * root = spaux->families[id];
  assert(root);
  spaux->families.erase(id);

  // TODO URGENT 
  // the SP needs to be able to register

  for (VentureValue * value : spaux->ownedValues[id])
  {
    omegaDB->flushQueue.emplace(value);
  }
  spaux->ownedValues.erase(id);

  omegaDB->spFamilyDBs[{vsp->makerNode,id}] = root;
  
  double weight = detachFamily(root,scaffold,omegaDB);
  return weight;
}

/* Does not erase from ventureFamilies */
double Trace::detachVentureFamily(Node * root,OmegaDB * omegaDB)
{
  assert(root);
  return detachFamily(root,nullptr,omegaDB);
}

double Trace::detachFamily(Node * node,
			   Scaffold * scaffold,
			   OmegaDB * omegaDB)
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
    weight += detachInternal(lookedUpNode,scaffold,omegaDB);
  }
  else
  {
    weight += unapply(node,scaffold,omegaDB);
    for (Node * operandNode : reverse(node->operandNodes))
    { weight += detachFamily(operandNode,scaffold,omegaDB); }
    weight += detachFamily(node->operatorNode,scaffold,omegaDB);
  }
  return weight;
}

double Trace::unapply(Node * node,
		      Scaffold * scaffold,
		      OmegaDB * omegaDB)
{
  double weight = 0;

  weight += unapplyPSP(node,scaffold,omegaDB);
  for (Node * esrParent : reverse(node->esrParents))
  { weight += detachInternal(esrParent,scaffold,omegaDB); }
  weight += unapplyPSP(node->requestNode,scaffold,omegaDB);

  return weight;
}
