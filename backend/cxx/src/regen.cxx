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

double Trace::regen(const vector<Node *> & border,
		    Scaffold * scaffold,
		    bool shouldRestore,
		    OmegaDB * omegaDB,
		    map<Node *,vector<double> > *gradients)
{
  assert(scaffold);
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold->isAbsorbing(node)) { weight += absorb(node,scaffold,shouldRestore,omegaDB,gradients); }
    else /* Terminal resampling */
    {
      weight += regenInternal(node,scaffold,shouldRestore,omegaDB,gradients);
      if (node->isObservation()) { weight += constrain(node,!shouldRestore); }
    }
  }
  return weight;
}

double Trace::regenParents(Node * node,
			   Scaffold * scaffold,
			   bool shouldRestore,
			   OmegaDB * omegaDB,
			   map<Node *,vector<double> > *gradients)
{
  assert(scaffold);

  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return regenInternal(node->lookedUpNode,scaffold,shouldRestore,omegaDB,gradients); }

  double weight = 0;

  weight += regenInternal(node->operatorNode,scaffold,shouldRestore,omegaDB,gradients);
  for (Node * operandNode : node->operandNodes)
  { weight += regenInternal(operandNode,scaffold,shouldRestore,omegaDB,gradients); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += regenInternal(node->requestNode,scaffold,shouldRestore,omegaDB,gradients);
    for (Node * esrParent : node->esrParents)
    { weight += regenInternal(esrParent,scaffold,shouldRestore,omegaDB,gradients); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold * scaffold,
		     bool shouldRestore,
		     OmegaDB * omegaDB,
		     map<Node *,vector<double> > *gradients)
{
  assert(scaffold);
  double weight = 0;
  weight += regenParents(node,scaffold,shouldRestore,omegaDB,gradients);
  weight += node->sp()->logDensity(node->getValue(),node);
  node->sp()->incorporate(node->getValue(),node);
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


double Trace::regenInternal(Node * node,
			    Scaffold * scaffold,
			    bool shouldRestore,
			    OmegaDB * omegaDB,
			    map<Node *,vector<double> > *gradients)
{
  if (!scaffold) { return 0; }
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    if (drgNode.regenCount == 0)
    {
      weight += regenParents(node,scaffold,shouldRestore,omegaDB,gradients);
      if (node->nodeType == NodeType::LOOKUP)
      { node->registerReference(node->lookedUpNode); }
      else /* Application node */
      { weight += applyPSP(node,scaffold,shouldRestore,omegaDB,gradients); }
      node->isActive = true;
    }
    drgNode.regenCount++;
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += regenInternal(node->sourceNode,scaffold,shouldRestore,omegaDB,gradients); }
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
		       bool shouldRestore,
		       OmegaDB * omegaDB,
		       map<Node *,vector<double> > *gradients)
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
    assert(omegaDB);
    if (scaffold && scaffold->isResampling(node)) { newValue = omegaDB->drgDB[node]; }
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
      sp->restoreAllLatents(node->spaux(),omegaDB->latentDBs[node->sp()]);
    }
  }
  else if (scaffold && scaffold->hasKernelFor(node))
  {
    VentureValue * oldValue = nullptr;
    if (omegaDB && omegaDB->drgDB.count(node)) { oldValue = omegaDB->drgDB[node]; }
    LKernel * k = scaffold->lkernels[node];

    /* Awkward. We are not letting the language know about the difference between
       regular LKernels and HSRKernels. We pass a latentDB no matter what, nullptr
       for the former. */
    LatentDB * latentDB = nullptr;
    if (omegaDB && omegaDB->latentDBs.count(node->sp())) { latentDB = omegaDB->latentDBs[node->sp()]; }

    newValue = k->simulate(oldValue,node,latentDB,rng);
    weight += k->weight(newValue,oldValue,node,latentDB);
    assert(isfinite(weight));

    VariationalLKernel * vlk = dynamic_cast<VariationalLKernel*>(k);
    if (vlk && gradients)
    {
      gradients->insert({node,vlk->gradientOfLogDensity(newValue,node)});
    }
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
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,shouldRestore,omegaDB,gradients); }


  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   bool shouldRestore,
			   OmegaDB * omegaDB,
			   map<Node *,vector<double> > *gradients)
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
      if (shouldRestore && omegaDB && omegaDB->spFamilyDBs.count({node->vsp()->makerNode, esr.id}))
      {
	esrParent = omegaDB->spFamilyDBs[{node->vsp()->makerNode, esr.id}];
	assert(esrParent);
	restoreSPFamily(node->vsp(),esr.id,esrParent,scaffold,omegaDB);
      }
      else
      {
	pair<double,Node*> p = evalFamily(esr.exp,esr.env,scaffold,omegaDB,false,gradients);      
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
    if (omegaDB && omegaDB->latentDBs.count(node->sp())) 
    { latentDB = omegaDB->latentDBs[node->sp()]; }
    assert(!shouldRestore || latentDB);
    weight += node->sp()->simulateLatents(node->spaux(),hsr,shouldRestore,latentDB,rng);
  }

  return weight;
}

pair<double, Node*> Trace::evalVentureFamily(size_t directiveID, 
					     VentureValue * exp,		     
					     map<Node *,vector<double> > *gradients)
{
  return evalFamily(exp,globalEnv,nullptr,nullptr,true,gradients);
}

double Trace::restoreSPFamily(VentureSP * vsp,
			      size_t id,
			      Node * root,
			      Scaffold * scaffold,
			      OmegaDB * omegaDB)
{
  Node * makerNode = vsp->makerNode;
  if (omegaDB->spOwnedValues.count(make_pair(makerNode,id)))
  {
    makerNode->madeSPAux->ownedValues[id] = omegaDB->spOwnedValues[make_pair(makerNode,id)];
  }
  restoreFamily(root,scaffold,omegaDB);
}


double Trace::restoreVentureFamily(Node * root)
{
  restoreFamily(root,nullptr,nullptr);
  return 0;
}

double Trace::restoreFamily(Node * node,
			    Scaffold * scaffold,
			    OmegaDB * omegaDB)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE)
  {
    // do nothing
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    regenInternal(node->lookedUpNode,scaffold,true,omegaDB,nullptr);
    node->reconnectLookup();
  }
  else
  {
    assert(node->operatorNode);
    restoreFamily(node->operatorNode,scaffold,omegaDB);
    for (Node * operandNode : node->operandNodes)
    { restoreFamily(operandNode,scaffold,omegaDB); }
    apply(node->requestNode,node,scaffold,true,omegaDB,nullptr);
  }
  return 0;
}


pair<double,Node*> Trace::evalFamily(VentureValue * exp, 
				     VentureEnvironment * env,
				     Scaffold * scaffold,
				     OmegaDB * omegaDB,
				     bool isDefinite,
				     map<Node *,vector<double> > *gradients)
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
    
      pair<double,Node*> p = evalFamily(listRef(list,0),env,scaffold,omegaDB,isDefinite,gradients);
      weight += p.first;
      operatorNode = p.second;
      
      for (uint8_t i = 1; i < listLength(list); ++i)
      {
	pair<double,Node*> p = evalFamily(listRef(list,i),env,scaffold,omegaDB,isDefinite,gradients);
	weight += p.first;
	operandNodes.push_back(p.second);
      }

      addApplicationEdges(operatorNode,operandNodes,requestNode,outputNode);
      weight += apply(requestNode,outputNode,scaffold,false,omegaDB,gradients);
    }
  }
  /* Variable lookup */
  else if (dynamic_cast<VentureSymbol*>(exp))
  {
    VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(exp);
    Node * lookedUpNode = env->findSymbol(vsym);
    assert(lookedUpNode);
    weight += regenInternal(lookedUpNode,scaffold,false,omegaDB,gradients);

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
		    bool shouldRestore,
		    OmegaDB * omegaDB,
		    map<Node *,vector<double> > *gradients)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,shouldRestore,omegaDB,gradients);
  
  if (requestNode->getValue())
  {
    /* Regenerate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(requestNode->getValue());
    for (ESR esr : requests->esrs)
    {
      Node * esrParent = requestNode->sp()->findFamily(esr.id,requestNode->spaux());
      assert(esrParent);
      weight += regenInternal(esrParent,scaffold,shouldRestore,omegaDB,gradients);
    }
  }

  requestNode->isActive = true;
  
  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,shouldRestore,omegaDB,gradients);
  outputNode->isActive = true;
  return weight;
}
