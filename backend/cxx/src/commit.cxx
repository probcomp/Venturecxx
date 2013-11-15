#include "node.h"
#include "value.h"
#include "env.h"
#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "omegadb.h"
#include "srs.h"
#include "flush.h"
#include "lkernel.h"
#include "utils.h"
#include <cmath>

#include <iostream>
#include <typeinfo>
#include "sps/mem.h"

double Trace::commit(const vector<Node *> & border,
		     Scaffold * scaffold,
		     Particle * omega)
{
  assert(scaffold);
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold->isAbsorbing(node)) { weight += absorb(node,scaffold,omega); }
    else /* Terminal resampling */
    {
      weight += commitInternal(node,scaffold,omega);
      /* Will no longer need this because we keep the node along with the info
	 that it does not own its value */
      if (node->isObservation()) { weight += constrain(node,!shouldRestore); }
    }
  }
  return weight;
}

/* Note: could be simplified by storing (or quickly computing) the direct parents. */
/* OPT: Since we never have a requestNode in a DRG without its outputNode, we ought
   to be able to only commit the operator and operands once. 
   (This may yield a substantial performance improvement.) */
double Trace::commitParents(Node * node,
			   Scaffold * scaffold,
			    Particle * omega)
{
  assert(scaffold);

  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return commitInternal(node->lookedUpNode,scaffold,omega); }

  double weight = 0;

  weight += commitInternal(node->operatorNode,scaffold,omega);
  for (Node * operandNode : node->operandNodes)
  { weight += commitInternal(operandNode,scaffold,omega); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += commitInternal(node->requestNode,scaffold,omega);
    for (Node * esrParent : node->esrParents)
    { weight += commitInternal(esrParent,scaffold,omega); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold * scaffold,
		     Particle * omega)
{
  assert(scaffold);
  double weight = 0;
  weight += commitParents(node,scaffold,omega);
  weight += node->sp()->logDensity(node->getValue(),node);
  return weight;
}

double Trace::constrain(Node * node,bool reclaimValue)
{
  assert(node->isObservation());
  return constrain(node,node->observedValue,reclaimValue);
}

double Trace::constrain(Node * node, VentureValue * value, bool reclaimValue)
{
  assert(node->isActive);
  if (node->isReference()) { return constrain(node->sourceNode,value,reclaimValue); }
  else
  {
    /* New restriction, to ensure that we did not propose to an
       observation node with a non-trivial kernel. TODO handle
       this in loadDefaultKernels instead. */
    assert(node->sp()->isRandomOutput);
    assert(node->sp()->canAbsorbOutput); // TODO temporary
    node->sp()->removeOutput(node->getValue(),node);

    if (reclaimValue) { delete node->getValue(); }

    /* TODO need to set this on restore, based on the FlushQueue */

    double weight = node->sp()->logDensityOutput(value,node);
    node->setValue(value);
    node->isConstrained = true;
    node->spOwnsValue = false;
    node->sp()->incorporateOutput(value,node);
    if (node->sp()->isRandomOutput) { 
      unregisterRandomChoice(node); 
      registerConstrainedChoice(node);
    }
    return weight;
  }
}


/* Note: no longer calls commit parents on REQUEST nodes. */
double Trace::commitInternal(Node * node,
			    Scaffold * scaffold,
			     Particle * omega)
{
  if (!scaffold) { return 0; }
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    if (drgNode.commitCount == 0)
    {
      weight += commitParents(node,scaffold,omega);
      if (node->nodeType == NodeType::LOOKUP)
      { node->registerReference(node->lookedUpNode); }
      else /* Application node */
      { weight += applyPSP(node,scaffold,omega); }
      node->isActive = true;
    }
    drgNode.commitCount++;
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += commitInternal(node->sourceNode,scaffold,omega); }
  }
  return weight;
}

/* TODO should load makerNode as well */
void Trace::processMadeSP(Node * node, bool isAAA)
{
  callCounts[{"processMadeSP",false}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(node->getValue());
  if (vsp->makerNode) { return; }

  callCounts[{"processMadeSPfull",false}]++;



  assert(vsp);

  SP * madeSP = vsp->sp;
  vsp->makerNode = node;
  if (!isAAA)
  {
    if (madeSP->hasAux()) { node->madeSPAux = madeSP->constructSPAux(); }
    if (madeSP->hasAEKernel) { registerAEKernel(vsp); }
  }
}


double Trace::applyPSP(Node * node,
		       Scaffold * scaffold,
		       Particle * omega)
{
  DPRINT("applyPSP: ", node->address.toString());
  callCounts[{"applyPSP",false}]++;
  SP * sp = node->sp();

  assert(node->isValid());
  assert(sp->isValid());

  /* Almost nothing needs to be done if this node is a ESRReference.*/
  if (node->nodeType == NodeType::OUTPUT && sp->isESRReference)
  {
    assert(!node->esrParents.empty());
    node->registerReference(node->esrParents[0]);
    return 0;
  }
  if (node->nodeType == NodeType::REQUEST && sp->isNullRequest())
  {
    return 0;
  }

  assert(!node->isReference());

  /* Otherwise we need to actually do things. */

  double weight = 0;

  VentureValue * newValue;

  if (shouldRestore)
  {
    assert(omega);
    if (scaffold && scaffold->isResampling(node)) { newValue = omega->drgDB[node]; }
    else 
    { 
      newValue = node->getValue(); 
      if (!newValue)
      {
	assert(newValue);
      }
    }
      
    /* If the kernel was an HSR kernel, then we restore all latents.
       TODO this could be made clearer. */
    if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
    {
      sp->restoreAllLatents(node->spaux(),omega->latentDBs[node->sp()]);
    }
  }
  else if (scaffold && scaffold->hasKernelFor(node))
  {
    VentureValue * oldValue = nullptr;
    if (omega && omega->drgDB.count(node)) { oldValue = omega->drgDB[node]; }
    LKernel * k = scaffold->lkernels[node];

    /* Awkward. We are not letting the language know about the difference between
       regular LKernels and HSRKernels. We pass a latentDB no matter what, nullptr
       for the former. */
    LatentDB * latentDB = nullptr;
    if (omega && omega->latentDBs.count(node->sp())) { latentDB = omega->latentDBs[node->sp()]; }

    newValue = k->simulate(oldValue,node,latentDB,rng);
    weight += k->weight(newValue,oldValue,node,latentDB);
    assert(isfinite(weight));

  }
  else
  {
    newValue = sp->simulate(node,rng);
  }
  assert(newValue);
  assert(newValue->isValid());
  node->setValue(newValue);

  sp->incorporate(newValue,node);

  if (dynamic_cast<VentureSP *>(node->getValue()))
  { processMadeSP(node,scaffold && scaffold->isAAA(node)); }
  if (node->sp()->isRandom(node->nodeType)) { registerRandomChoice(node); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,omega); }


  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   Particle * omega)
{
  /* Null request does not bother malloc-ing */
  if (!node->getValue()) { return 0; }
  double weight = 0;

  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  /* First evaluate ESRs. */
  for (ESR esr : requests->esrs)
  {
    assert(node->spaux()->isValid());
    Node * esrParent;
    if (!node->spaux()->families.count(esr.id))
    {
      if (shouldRestore && omega && omega->spFamilyDBs.count({node->vsp()->makerNode, esr.id}))
      {
	esrParent = omega->spFamilyDBs[{node->vsp()->makerNode, esr.id}];
	assert(esrParent);
	restoreSPFamily(node->vsp(),esr.id,esrParent,scaffold,omega);
      }
      else
      {
	pair<double,Node*> p = evalFamily(esr.exp,esr.env,scaffold,omega,false);      
	weight += p.first;
	esrParent = p.second;
      }
      node->sp()->registerFamily(esr.id, esrParent, node->spaux());
    }
    else
    {
      esrParent = node->spaux()->families[esr.id];
      assert(esrParent->isValid());

      // right now only MSP's share
      // (guard against hash collisions)
      assert(dynamic_cast<MSP*>(node->sp()));
      
    }
    Node::addESREdge(esrParent,node->outputNode);
  }

  /* Next evaluate HSRs. */
  for (HSR * hsr : requests->hsrs)
  {
    LatentDB * latentDB = nullptr;
    if (omega && omega->latentDBs.count(node->sp())) 
    { latentDB = omega->latentDBs[node->sp()]; }
    assert(!shouldRestore || latentDB);
    weight += node->sp()->simulateLatents(node->spaux(),hsr,latentDB,rng);
  }

  return weight;
}

pair<double, Node*> Trace::evalVentureFamily(size_t directiveID, 
					     VentureValue * exp)
{
  return evalFamily(exp,globalEnv,nullptr,nullptr,true);
}

double Trace::restoreSPFamily(VentureSP * vsp,
			      size_t id,
			      Node * root,
			      Scaffold * scaffold,
			      Particle * omega)
{
  Node * makerNode = vsp->makerNode;
  if (omega->spOwnedValues.count(make_pair(makerNode,id)))
  {
    makerNode->madeSPAux->ownedValues[id] = omega->spOwnedValues[make_pair(makerNode,id)];
  }
  restoreFamily(root,scaffold,omega);
}


double Trace::restoreVentureFamily(Node * root)
{
  restoreFamily(root,nullptr,nullptr);
  return 0;
}

double Trace::restoreFamily(Node * node,
			    Scaffold * scaffold,
			    Particle * omega)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE)
  {
    // do nothing
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    commitInternal(node->lookedUpNode,scaffold,true,omega,nullptr);
    node->reconnectLookup();
  }
  else
  {
    assert(node->operatorNode);
    restoreFamily(node->operatorNode,scaffold,omega);
    for (Node * operandNode : node->operandNodes)
    { restoreFamily(operandNode,scaffold,omega); }
    apply(node->requestNode,node,scaffold,true,omega,nullptr);
  }
  return 0;
}


pair<double,Node*> Trace::evalFamily(VentureValue * exp, 
				     VentureEnvironment * env,
				     Scaffold * scaffold,
				     Particle * omega)
{
  DPRINT("eval: ", addr.toString());
  double weight = 0;
  Node * node = nullptr;
  assert(exp);
  if (dynamic_cast<VenturePair*>(exp))
  {
    VentureList * list = dynamic_cast<VentureList*>(exp);
    VentureSymbol * car = dynamic_cast<VentureSymbol*>(listRef(list,0));
 
    if (car && car->sym == "quote")
    {
      node = new Node(NodeType::VALUE, nullptr);
      node->setValue(listRef(list,1));
      node->isActive = true;
    }
    /* Application */
    else
    {
      Node * requestNode = new Node(NodeType::REQUEST,nullptr,env);
      Node * outputNode = new Node(NodeType::OUTPUT,nullptr,env);
      node = outputNode;

      Node * operatorNode;
      vector<Node *> operandNodes;
    
      pair<double,Node*> p = evalFamily(listRef(list,0),env,scaffold,omega,isDefinite);
      weight += p.first;
      operatorNode = p.second;
      
      for (uint8_t i = 1; i < listLength(list); ++i)
      {
	pair<double,Node*> p = evalFamily(listRef(list,i),env,scaffold,omega,isDefinite);
	weight += p.first;
	operandNodes.push_back(p.second);
      }

      addApplicationEdges(operatorNode,operandNodes,requestNode,outputNode);
      weight += apply(requestNode,outputNode,scaffold,false,omega);
    }
  }
  /* Variable lookup */
  else if (dynamic_cast<VentureSymbol*>(exp))
  {
    VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(exp);
    Node * lookedUpNode = env->findSymbol(vsym);
    assert(lookedUpNode);
    weight += commitInternal(lookedUpNode,scaffold,false,omega);

    node = new Node(NodeType::LOOKUP,nullptr);
    Node::addLookupEdge(lookedUpNode,node);
    node->registerReference(lookedUpNode);
    node->isActive = true;
  }
  /* Self-evaluating */
  else
  {
    node = new Node(NodeType::VALUE,exp);
    node->isActive = true;
  }
  assert(node);
  return {weight,node};
}

double Trace::apply(Node * requestNode,
		    Node * outputNode,
		    Scaffold * scaffold,
		    Particle * omega)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,omega);
  
  if (requestNode->getValue())
  {
    /* Commiterate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(requestNode->getValue());
    for (ESR esr : requests->esrs)
    {
      Node * esrParent = requestNode->sp()->findFamily(esr.id,requestNode->spaux());
      assert(esrParent);
      weight += commitInternal(esrParent,scaffold,omega);
    }
  }

  requestNode->isActive = true;
  
  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,omega);
  outputNode->isActive = true;
  return weight;
}
