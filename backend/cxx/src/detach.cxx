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
    vector<Node *> esrParents = getESRParents(node);
    for (Node * esrParent : reverse(esrParents))
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
  getSP(node)->remove(getValue(node),getArgs(node));
  weight += getSP(node)->logDensity(getValue(node),getArgs(node));
  weight += detachParents(node,scaffold,omegaDB);
  return weight;
}

double Trace::unconstrain(Node * node, bool giveOwnershipToSP)
{
  assert(node->isActive);
  if (isReference(node))
  { return unconstrain(node->sourceNode,giveOwnershipToSP); }
  else
  {
    if (getSP(node)->isRandomOutput) { 
      unregisterConstrainedChoice(node);
      registerRandomChoice(node);
    }
    getSP(node)->removeOutput(getValue(node),getArgs(node));
    double logDensity = getSP(node)->logDensityOutput(getValue(node),getArgs(node));
    node->isConstrained = false;
    node->spOwnsValue = giveOwnershipToSP;
    getSP(node)->incorporateOutput(getValue(node),getArgs(node));
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
    if (isReference(node) && scaffold->isAAA(node->sourceNode))
    { weight += detachInternal(node->sourceNode,scaffold,omegaDB); }
  }
  return weight;
}

void Trace::teardownMadeSP(Node * node, bool isAAA,OmegaDB * omegaDB)
{
  callCounts[{"processMadeSP",true}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(getValue(node));

  if (vsp->makerNode != node) { return; }

  callCounts[{"processMadeSPfull",true}]++;

  vsp->makerNode = nullptr;

  SP * madeSP = vsp->sp;

  if (!isAAA)
  {
    if (madeSP->hasAEKernel) { unregisterAEKernel(vsp); }
    if (madeSP->hasAux()) 
    { 
//      omegaDB->flushQueue.emplace(madeSP,node->madeSPAux); 
      delete node->madeSPAux; 
      node->madeSPAux = nullptr;
    }
  }
}


double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold,
			 OmegaDB * omegaDB)
{
  callCounts[{"applyPSP",true}]++;

  assert(node->isValid());
  assert(getSP(node)->isValid());



  if (node->nodeType == NodeType::OUTPUT && getSP(node)->isESRReference) 
  { 
    node->sourceNode = nullptr;
    return 0; 
  }
  if (node->nodeType == NodeType::REQUEST && getSP(node)->isNullRequest()) { return 0; }

  
  assert(getValue(node)->isValid());

  if (node->nodeType == NodeType::REQUEST) { unevalRequests(node,scaffold,omegaDB); }
  if (getSP(node)->isRandom(node->nodeType)) { 
    unregisterRandomChoice(node); 
  }
  
  if (dynamic_cast<VentureSP*>(getValue(node)))
  { teardownMadeSP(node,scaffold && scaffold->isAAA(node),omegaDB); }

  SP * sp = getSP(node);
  double weight = 0;

  sp->remove(getValue(node),getArgs(node));

  if (scaffold && scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(getValue(node),getArgs(node),nullptr); }

  if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
  { 
    pair<double, LatentDB *> p = getSP(node)->detachAllLatents(getSPAux(node));
    weight += p.first;
    assert(!omegaDB->latentDBs.count(getSP(node)));
    omegaDB->latentDBs.insert({getSP(node),p.second});
  }



  if (node->spOwnsValue) 
  { 

    omegaDB->flushQueue.emplace(getSP(node),getValue(node),node->nodeType); 
  }

  if (scaffold && scaffold->isResampling(node))
  { omegaDB->drgDB[node] = getValue(node);  node->clearValue(); }


  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold,
			     OmegaDB * omegaDB)
{
  assert(node->nodeType == NodeType::REQUEST);
  if (!getValue(node)) { return 0; }

  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(getValue(node));

  if (!requests->hsrs.empty() && !omegaDB->latentDBs.count(getSP(node)))
  { omegaDB->latentDBs[getSP(node)] = getSP(node)->constructLatentDB(); }

  for (HSR * hsr : reverse(requests->hsrs))
  {
    LatentDB * latentDB = omegaDB->latentDBs[getSP(node)];
    weight += getSP(node)->detachLatents(getSPAux(node),hsr,latentDB);
  }

  for (ESR esr : reverse(requests->esrs))
  {
    assert(getSPAux(node));
    assert(getSPAux(node)->isValid());
    assert(!getESRParents(node->outputNode).empty());
    // TODO give trace responsibility
    Node * esrParent = node->outputNode->removeLastESREdge();
    assert(esrParent);
    assert(esrParent->isValid());

    if (esrParent->numRequests == 0)
    { 
      weight += detachSPFamily(getVSP(node),esr.id,scaffold,omegaDB); 
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

  if (!spaux->ownedValues.empty())
  {
    omegaDB->spOwnedValues[make_pair(vsp->makerNode,id)] = spaux->ownedValues[id];
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
  vector<Node *> esrParents = getESRParents(node);
  for (Node * esrParent : reverse(esrParents))
  { weight += detachInternal(esrParent,scaffold,omegaDB); }
  weight += unapplyPSP(node->requestNode,scaffold,omegaDB);

  return weight;
}
