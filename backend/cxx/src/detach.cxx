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

double Trace::detach(const vector<Node *> & border,
		     Scaffold * scaffold)

{
//  cout << "DETACH" << endl;
  assert(scaffold);

  double weight = 0;

  for (Node * node : reverse(border))
  {
    if (scaffold->isAbsorbing(node))
    { 
      weight += unabsorb(node,scaffold); 
    }
    else
    {
      assert(scaffold->isResampling(node));
      if (node->isObservation()) 
      { 
	weight += unconstrain(node,false);
      }
      weight += detachInternal(node,scaffold);
    }
  }
  
  return weight;
}

double Trace::detachParents(Node * node,
			    Scaffold * scaffold)
{
  assert(scaffold);
  double weight = 0;
  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return detachInternal(node->lookedUpNode,scaffold); }

  if (node->nodeType == NodeType::OUTPUT)
  {
    vector<Node *> esrParents = getESRParents(node);
    for (Node * esrParent : reverse(esrParents))
    { weight += detachInternal(esrParent,scaffold); }
    weight += detachInternal(node->requestNode,scaffold);
  }
  for (Node * operandNode : reverse(node->operandNodes))
  { weight += detachInternal(operandNode,scaffold); }
  weight += detachInternal(node->operatorNode,scaffold);
  return weight;
}

double Trace::unabsorb(Node * node,
		       Scaffold * scaffold)
{
  assert(scaffold);
  preUnabsorb(node);
  double weight = 0;
  getSP(node)->remove(getValue(node),getArgs(node));
  weight += getSP(node)->logDensity(getValue(node),getArgs(node));
  weight += detachParents(node,scaffold);
  return weight;
}

double Trace::unconstrain(Node * node, bool giveOwnershipToSP)
{
  if (isReference(node))
  { return unconstrain(getSourceNode(node),giveOwnershipToSP); }
  else
  {
    assert(getSP(node)->isRandomOutput);
    preUnconstrain(node);
    if (getSP(node)->isRandomOutput) { unconstrainChoice(node); }
    getSP(node)->removeOutput(getValue(node),getArgs(node));
    double logDensity = getSP(node)->logDensityOutput(getValue(node),getArgs(node));
    clearConstrained(node);
    if (giveOwnershipToSP) { setNodeOwnsValue(node); }
    getSP(node)->incorporateOutput(getValue(node),getArgs(node));
    return logDensity;
  }
}

double Trace::detachInternal(Node * node,
			     Scaffold * scaffold)
{
  if (!scaffold) { return 0; }
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    decrementRegenCount(node,scaffold);
    if (getRegenCount(node,scaffold) < 0)
    {
      cout << "\n\n\n\n\n---RegenCount < 0! (" << node << ")---\n\n\n" << endl;
      scaffold->show();
    }

    assert(getRegenCount(node,scaffold) >= 0);
    if (getRegenCount(node,scaffold) == 0)
    {
      if (node->isApplication())
      { 
	weight += unapplyPSP(node,scaffold); 
      }

      weight += detachParents(node,scaffold);
    }
  }
  return weight;
}

void Trace::teardownMadeSP(Node * node, 
			   bool isAAA)
{
  callCounts[{"processMadeSP",true}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(getValue(node));

  if (vsp->makerNode != node) { return; }

  callCounts[{"processMadeSPfull",true}]++;

  SP * madeSP = vsp->sp;

  if (!isAAA)
  {
    if (madeSP->hasAEKernel) { unregisterAEKernel(vsp); }
    if (madeSP->hasAux()) 
    { 
      clearVSPMakerNode(vsp,node);
      detachMadeSPAux(node);
    }
  }
}


double Trace::unapplyPSP(Node * node,
			 Scaffold * scaffold)
{
  callCounts[{"applyPSP",true}]++;
  cout << "unapplyPSP @ " << node->address << endl;
  assert(node->isValid());
  assert(getSP(node)->isValid());
  preUnapplyPSP(node);

  if (node->nodeType == NodeType::OUTPUT && getSP(node)->isESRReference) 
  { 
    clearSourceNode(node);
    return 0; 
  }
  if (node->nodeType == NodeType::REQUEST && getSP(node)->isNullRequest()) { return 0; }
  
  assert(getValue(node)->isValid());

  if (node->nodeType == NodeType::REQUEST) { unevalRequests(node,scaffold); }
  if (getSP(node)->isRandom(node->nodeType)) { unregisterRandomChoice(node); }
  
  if (dynamic_cast<VentureSP*>(getValue(node)))
  { teardownMadeSP(node,scaffold && scaffold->isAAA(node)); }

  SP * sp = getSP(node);
  double weight = 0;

  sp->remove(getValue(node),getArgs(node));

  if (scaffold && scaffold->hasKernelFor(node))
  { weight += scaffold->lkernels[node]->reverseWeight(getValue(node),getArgs(node),nullptr); }

  if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
  { 
    pair<double, LatentDB *> p = getSP(node)->detachAllLatents(getSPAux(node));
    weight += p.first;
    extractLatentDB(getSP(node),p.second);
  }


  if (node->spOwnsValue) 
  { 
    registerGarbage(getSP(node),getValue(node),node->nodeType);
  }

  if (scaffold && scaffold->isResampling(node))
  { 
    extractValue(node,getValue(node));
    clearValue(node); 
  }

  return weight;
}


double Trace::unevalRequests(Node * node,
			     Scaffold * scaffold)
{
  assert(node->nodeType == NodeType::REQUEST);
  if (!getValue(node)) { return 0; }

  preUnevalRequests(node);
  double weight = 0;
  VentureRequest * requests = dynamic_cast<VentureRequest *>(getValue(node));

  if (!requests->hsrs.empty()) 
  { 
    prepareLatentDB(getSP(node));
  }

  for (HSR * hsr : reverse(requests->hsrs))
  {
    LatentDB * latentDB = getLatentDB(getSP(node)); 
    weight += getSP(node)->detachLatents(getSPAux(node),hsr,latentDB);
    processDetachedLatentDB(getSP(node),latentDB); 
  }

  for (ESR esr : reverse(requests->esrs))
  {
//    cout << "unevalRequest @ " << node->address;

    assert(getSPAux(node));
    assert(getSPAux(node)->isValid());
    assert(!getESRParents(node->outputNode).empty());

    Node * esrParent = removeLastESREdge(node->outputNode);
//    cout << " found @ " << esrParent->address << endl;
    assert(esrParent);
    assert(esrParent->isValid());

    if (esrParent->numRequests == 0)
    { 
//      cout << "--detached--" << endl;
      weight += detachSPFamily(getVSP(node),esr.id,scaffold); 
    }
  }

  return weight;
}

double Trace::detachSPFamily(VentureSP * vsp,
			     size_t id,
			     Scaffold * scaffold)
{
  assert(vsp);
  assert(vsp->makerNode);
  assert(vsp->makerNode->madeSPAux);
  SPAux * spaux = getMadeSPAux(vsp->makerNode);
//  cout << "detachFamily(" << spaux << endl;
  Node * root = spaux->families[id];
  assert(root);
  spaux->families.erase(id);

  if (!spaux->ownedValues.empty()) 
  { 
    registerSPOwnedValues(vsp->makerNode,id,spaux->ownedValues[id]);
  }

  spaux->ownedValues.erase(id);

  registerSPFamily(vsp->makerNode,id,root);

  
  return detachFamily(root,scaffold);
}

/* Does not erase from ventureFamilies */
double Trace::detachVentureFamily(Node * root)
{
  assert(root);
  return detachFamily(root,nullptr);
}

double Trace::detachFamily(Node * node,
			   Scaffold * scaffold)
{
//  cout << "uneval: " << node->address << endl;
  assert(node);
  double weight = 0;
  
  if (node->nodeType == NodeType::VALUE) 
  { 
    // do nothing! (finally!)
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    Node * lookedUpNode = node->lookedUpNode;
    disconnectLookup(node);
    weight += detachInternal(lookedUpNode,scaffold);
  }
  else
  {
    weight += unapply(node,scaffold);
    for (Node * operandNode : reverse(node->operandNodes))
    { weight += detachFamily(operandNode,scaffold); }
    weight += detachFamily(node->operatorNode,scaffold);
  }
  return weight;
}

double Trace::unapply(Node * node,
		      Scaffold * scaffold)
{
  double weight = 0;

  weight += unapplyPSP(node,scaffold);
  vector<Node *> esrParents = getESRParents(node);
  for (Node * esrParent : reverse(esrParents))
  { weight += detachInternal(esrParent,scaffold); }
  weight += unapplyPSP(node->requestNode,scaffold);

  return weight;
}
