#include "trace.h"
#include "omegadb.h"

#include <iostream>
#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

std::pair<double, OmegaDB> Trace::detach(const std::vector<Node *> & border,
					 Scaffold * scaffold)
{

  double weight = 0;
  OmegaDB omegaDB;

  for (Node * node : reverse(border))
  {
    if (scaffold->isAbsorbing(node))
    { weight += unabsorb(node,scaffold,omegaDB); }
    else
    {
      assert(scaffold->isResampling(node));
      if (node->isObservation()) { weight += unconstrain(node); }
      weight += detachInternal(node,scaffold,omegaDB);
    }
  }
  
  return std::make_pair(weight,omegaDB);
}

double Trace::detachParents(Node * node,
			    Scaffold * scaffold,
			    OmegaDB & omegaDB)
{
  double weight = 0;
  assert(node->nodeType != NodeType::VALUE);
  assert(node->nodeType != NodeType::FAMILY_ENV);

  if (node->nodeType == NodeType::LOOKUP)
  { return detachInternal(node->lookedUpNode,scaffold,omegaDB); }

  if (node->nodeType == NodeType::OUTPUT)
  {
    for (Node * csrParent : reverse(node->csrParents))
    { weight += detachInternal(csrParent,scaffold,omegaDB); }
    weight += detachInternal(node->requestNode,scaffold,omegaDB);
  }
  for (Node * operandNode : reverse(node->operandNodes))
  { weight += detachInternal(operandNode,scaffold,omegaDB); }
  weight += detachInternal(node->operatorNode,scaffold,omegaDB);
  return weight;
}

double Trace::unabsorb(Node * node,
		       Scaffold * scaffold,
		       OmegaDB & omegaDB)
{
  double weight = 0;
  node->sp->remove(node->getValue(),node);
  weight += node->sp->logDensity(node->getValue(),node);
  weight += detachParents(node,scaffold,omegaDB);
  return weight;
}

double Trace::unconstrain(Node * node)
{
  assert(node->isActive);
  if (node->isReference())
  { return unconstrain(node->sourceNode); }
  else
  {
    if (node->sp->isRandomOutput) { registerRandomChoice(node); }
    node->sp->removeOutput(node->getValue(),node);
    double logDensity = node->sp->logDensityOutput(node->getValue(),node);
    node->isConstrained = false;
    node->sp->incorporateOutput(node->getValue(),node);
    return logDensity;
  }
}

double Trace::detachInternal(Node * node,
			     Scaffold * scaffold,
			     OmegaDB & omegaDB)
{
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    drgNode.regenCount--;
    assert(drgNode.regenCount >= 0);
    if (drgNode.regenCount == 0)
    {
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

double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold,
			 OmegaDB & omegaDB)
{
  double weight = 0;

  if (node->nodeType == NodeType::REQUEST) 
  { unevalRequests(node,scaffold,omegaDB); }

  if (node->sp->isRandom(node->nodeType) && !node->isConstrained)
  { unregisterRandomChoice(node); }

  node->sp->remove(node->getValue(),node);
      
  /* This is where I need to setup a latentDB. */
  if (scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(node->getValue(),node,nullptr); }

  /* TODO this is where we would call "unsample" to implement token-based
     restore. */
  omegaDB.rcs[node->address] = node->getValue();
  node->isActive = false;
  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold,
			     OmegaDB & omegaDB)
{
  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  if (!requests->esrs.empty() && !omegaDB.latentDBsbySP.count(node->sp))
  { omegaDB.latentDBsbySP[node->sp] = node->sp->constructLatentDB(); }

  for (ESR * esr : reverse(requests->esrs))
  {
    LatentDB * latentDB = omegaDB.latentDBsbySP[node->sp];
    weight += node->sp->detachLatents(node->spAux,esr,latentDB);
  }

  assert(node->nodeType == NodeType::REQUEST);

  /* Subtle optimization, iterating over the csrParents instead of the
     csrs themselves. */
  for (Node * csrParent : reverse(node->outputNode->csrParents))
  {
    Node::removeCSREdge1D(csrParent,node->outputNode);
    if (csrParent->numRequests == 0) 
    { weight += unevalFamily(csrParent,scaffold,omegaDB); }
  }
  /* We only removed the edges in one direction so far. (Premature optimization) */
  node->outputNode->csrParents.clear();

  return weight;
}

double Trace::unevalFamily(Node * node,
			   Scaffold * scaffold,
			   OmegaDB & omegaDB)
{
  double weight = uneval(node,scaffold,omegaDB);
  Address familyEnvAddr = node->address.getFamilyEnvAddress();

  if (containsAddr(familyEnvAddr))
  { destroyNode(getNode(familyEnvAddr)); }
  return weight;
}

double Trace::uneval(Node * node,
		     Scaffold * scaffold,
		     OmegaDB & omegaDB)
{
  double weight = 0;
  if (node->nodeType == NodeType::VALUE) { destroyNode(node); }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    Node * lookedUpNode = node->lookedUpNode;
    node->disconnectLookup();
    destroyNode(node);
    weight += detachInternal(lookedUpNode,scaffold,omegaDB);
  }
  else
  {
    weight += unapply(node,scaffold,omegaDB);
    for (Node * operandNode : node->operandNodes)
    { weight += uneval(operandNode,scaffold,omegaDB); }
    weight += uneval(node->operatorNode,scaffold,omegaDB);
  }
  destroyNode(node->requestNode);
  destroyNode(node);
  return weight;
}

double Trace::unapply(Node * node,
		      Scaffold * scaffold,
		      OmegaDB & omegaDB)
{
  double weight = 0;
  /* Copy */
  std::vector<Node *> csrParents = node->csrParents;

  weight += unapplyPSP(node,scaffold,omegaDB);
  for (Node * csrParent : reverse(csrParents))
  { weight += detachInternal(csrParent,scaffold,omegaDB); }
  weight += unapplyPSP(node->requestNode,scaffold,omegaDB);

  return weight;
}
