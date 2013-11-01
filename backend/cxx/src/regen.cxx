#include "node.h"
#include "value.h"

#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "omegadb.h"
#include "srs.h"
#include "flush.h"
#include "lkernel.h"

#include <iostream>
#include <typeinfo>


double Trace::regen(const vector<Node *> & border,
		    Scaffold & scaffold,
		    bool shouldRestore,
		    OmegaDB & omegaDB)
{
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold.isAbsorbing(node)) { weight += absorb(node,scaffold,shouldRestore,omegaDB); }
    else /* Terminal resampling */
    {
      weight += regenInternal(node,scaffold,shouldRestore,omegaDB);
      /* Will no longer need this because we keep the node along with the info
	 that it does not own its value */
      if (node->isObservation()) { weight += constrain(node,!shouldRestore); }
    }
  }
  return weight;
}

/* Note: could be simplified by storing (or quickly computing) the direct parents. */
/* OPT: Since we never have a requestNode in a DRG without its outputNode, we ought
   to be able to only regen the operator and operands once. 
   (This may yield a substantial performance improvement.) */
double Trace::regenParents(Node * node,
			   Scaffold & scaffold,
			   bool shouldRestore,
			   OmegaDB & omegaDB)
{
  assert(node->nodeType != NodeType::VALUE);
  assert(node->nodeType != NodeType::FAMILY_ENV);

  if (node->nodeType == NodeType::LOOKUP)
  { return regenInternal(node->lookedUpNode,scaffold,shouldRestore,omegaDB); }

  double weight = 0;

  weight += regenInternal(node->operatorNode,scaffold,shouldRestore,omegaDB);
  for (Node * operandNode : node->operandNodes)
  { weight += regenInternal(operandNode,scaffold,shouldRestore,omegaDB); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += regenInternal(node->requestNode,scaffold,shouldRestore,omegaDB);
    for (Node * esrParent : node->esrParents)
    { weight += regenInternal(esrParent,scaffold,shouldRestore,omegaDB); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold & scaffold,
		     bool shouldRestore,
		     OmegaDB & omegaDB)
{
  double weight = 0;
  weight += regenParents(node,scaffold,shouldRestore,omegaDB);
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
    node->ownsValue = false;
    node->sp()->incorporateOutput(value,node);
    if (node->sp()->isRandomOutput) { unregisterRandomChoice(node); }
    return weight;
  }
}


/* Note: no longer calls regen parents on REQUEST nodes. */
double Trace::regenInternal(Node * node,
			    Scaffold & scaffold,
			    bool shouldRestore,
			    OmegaDB & omegaDB)
{
  double weight = 0;

  if (scaffold.isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold.drg[node];
    if (drgNode.regenCount == 0)
    {
      weight += regenParents(node,scaffold,shouldRestore,omegaDB);
      if (node->nodeType == NodeType::LOOKUP)
      { node->registerReference(node->lookedUpNode); }
      else /* Application node */
      { weight += applyPSP(node,scaffold,shouldRestore,omegaDB); }
      node->isActive = true;
    }
    drgNode.regenCount++;
  }
  else if (scaffold.hasAAANodes)
  {
    if (node->isReference() && scaffold.isAAA(node->sourceNode))
    { weight += regenInternal(node->sourceNode,scaffold,shouldRestore,omegaDB); }
  }
  return weight;
}

void Trace::processMadeSP(Node * node)
{
  VentureSP * vsp = dynamic_cast<VentureSP *>(node->getValue());
  assert(vsp);
  SP * madeSP = vsp->sp;
  if (madeSP->hasAux()) 
  { 
    node->madeSPAux = madeSP->constructSPAux(); 
  }
  if (madeSP->hasAEKernel) { registerAEKernel(vsp); }
}


double Trace::applyPSP(Node * node,
		       Scaffold & scaffold,
		       bool shouldRestore,
		       OmegaDB & omegaDB)
{
  DPRINT("applyPSP: ", node->address.toString());

  SP * sp = node->sp();

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

  /* Otherwise we need to actually do things. */

  double weight = 0;

  VentureValue * newValue;

  if (shouldRestore)
  {
    if (scaffold.isResampling(node)) { newValue = omegaDB.drgDB[node]; }
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
    if (sp->makesHSRs && scaffold.isAAA(node))
    {
      sp->restoreAllLatents(node->spaux(),omegaDB.latentDBs[node]);
    }
  }
  else if (scaffold.hasKernelFor(node))
  {
    VentureValue * oldValue = omegaDB.drgDB[node];
    LKernel * k = scaffold.lkernels[node];

    /* Awkward. We are not letting the language know about the difference between
       regular LKernels and HSRKernels. We pass a latentDB no matter what, nullptr
       for the former. */
    LatentDB * latentDB = nullptr;
    if (omegaDB.latentDBs.count(node)) { latentDB = omegaDB.latentDBs[node]; }

    newValue = k->simulate(oldValue,node,latentDB,rng);
    weight += k->weight(newValue,oldValue,node,latentDB);
  }
  else
  {
    newValue = sp->simulate(node,rng);
  }
  assert(newValue);
  node->setValue(newValue);

  sp->incorporate(newValue,node);

  if (dynamic_cast<VentureSP *>(node->getValue()) && !node->isReference() && !scaffold.isAAA(node)) 
  { processMadeSP(node); }
  if (node->sp()->isRandom(node->nodeType)) { registerRandomChoice(node); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,shouldRestore,omegaDB); }


  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold & scaffold,
			   bool shouldRestore,
			   OmegaDB & omegaDB)
{
  /* Null request does not bother malloc-ing */
  if (!node->getValue()) { return 0; }
  double weight = 0;

  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->getValue());

  /* First evaluate ESRs. */
  for (ESR esr : requests->esrs)
  {
    Node * esrParent = node->sp()->findFamily(esr.id, node->spaux());
    if (!esrParent)
    {
      if (shouldRestore && omegaDB.spFamilyDBs.count({node->vsp()->makerNode, esr.id}))
      {
	esrParent = omegaDB.spFamilyDBs[{node->vsp()->makerNode, esr.id}];
	assert(esrParent);
	restoreSPFamily(esrParent,scaffold,omegaDB);
      }
      else
      {
	pair<double,Node*> p = evalSPFamily(esr.exp,esr.env,scaffold,omegaDB);      
	weight += p.first;
	esrParent = p.second;
      }
      node->sp()->registerFamily(esr.id, esrParent, node->spaux());
    }
    Node::addESREdge(esrParent,node->outputNode);
  }

  /* Next evaluate HSRs. */
  for (HSR * hsr : requests->hsrs)
  {
    LatentDB * latentDB = nullptr;
    if (omegaDB.latentDBs.count(node->vsp()->makerNode)) 
    { latentDB = omegaDB.latentDBs[node->vsp()->makerNode]; }
    assert(!shouldRestore || latentDB);
    weight += node->sp()->simulateLatents(node->spaux(),hsr,shouldRestore,latentDB,rng);
  }

  return weight;
}

pair<double,Node*> Trace::evalSPFamily(Expression & exp,
				       Environment & env,
				       Scaffold & scaffold,
				       OmegaDB & omegaDB)
{
  Node * familyEnvNode = new Node(NodeType::FAMILY_ENV, new VentureEnvironment(env));
  return evalFamily(exp,familyEnvNode,scaffold,omegaDB,false);
}


double Trace::restoreSPFamily(Node * root,
			      Scaffold & scaffold,
			      OmegaDB & omegaDB)
{
  restoreFamily(root,scaffold,omegaDB);
  return 0;
}

pair<double, Node*> Trace::evalVentureFamily(size_t directiveID, Expression & exp)
{
  Scaffold scaffold;
  OmegaDB omegaDB;
  return evalFamily(exp,globalEnvNode,scaffold,omegaDB,true);
}

double Trace::restoreVentureFamily(Node * root)
{
  Scaffold scaffold;
  OmegaDB omegaDB;
  restoreFamily(root,scaffold,omegaDB);
  return 0;
}

double Trace::restoreFamily(Node * node,
			    Scaffold & scaffold,
			    OmegaDB & omegaDB)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE)
  {
    if (dynamic_cast<VentureSP *>(node->getValue()))
    { processMadeSP(node); }
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    regenInternal(node->lookedUpNode,scaffold,true,omegaDB);
    node->reconnectLookup();
  }
  else
  {
    assert(node->operatorNode);
    restoreFamily(node->operatorNode,scaffold,omegaDB);
    for (Node * operandNode : node->operandNodes)
    { restoreFamily(operandNode,scaffold,omegaDB); }
    apply(node->requestNode,node,scaffold,true,omegaDB);
  }
  return 0;
}


pair<double,Node*> Trace::evalFamily(Expression & exp, 
				     Node * familyEnvNode,
				     Scaffold & scaffold,
				     OmegaDB & omegaDB,
				     bool isDefinite)
{
  DPRINT("eval: ", addr.toString());
  double weight = 0;
  Node * node;
  switch (exp.expType)
  {
  case ExpType::VALUE:
  {
    node = new Node(NodeType::VALUE,exp.value,familyEnvNode);
    node->isActive = true;
    node->ownsValue = isDefinite;
    break;
  }
  case ExpType::VARIABLE:
  {
    Node * lookedUpNode = familyEnvNode->getEnvironment()->findSymbol(exp.sym);
    assert(lookedUpNode);
    /* What is the right flag? (1) Value defined? and (2) connected to trace?
       Or nodeStatus = IN_TRACE, UNDEFINED, IN_DB */
//    assert(lookedUpNode->isActive);
    weight += regenInternal(lookedUpNode,scaffold,false,omegaDB);

    node = new Node(NodeType::LOOKUP,nullptr,familyEnvNode);
    Node::addLookupEdge(lookedUpNode,node);
    node->registerReference(lookedUpNode);
    node->isActive = true;
    break;
  }
  case ExpType::LAMBDA:
  {
    node = new Node(NodeType::VALUE, nullptr, familyEnvNode);
    /* The CSP owns the expression iff it is in a VentureFamily */
    node->setValue(new VentureSP(node,new CSP(exp.getIDs(),exp.exps[2],familyEnvNode,isDefinite)));
    processMadeSP(node);
    node->isActive = true;
    break;
  }
  case ExpType::APPLICATION:
  {
    Node * requestNode = new Node(NodeType::REQUEST,nullptr,familyEnvNode);
    Node * outputNode = new Node(NodeType::OUTPUT,nullptr,familyEnvNode);
    node = outputNode;

    Node * operatorNode;
    vector<Node *> operandNodes;
    
    pair<double,Node*> p = evalFamily(exp.exps[0],familyEnvNode,scaffold,omegaDB,isDefinite);
    weight += p.first;
    operatorNode = p.second;
      
    for (uint8_t i = 1; i < exp.exps.size(); ++i)
    {
      pair<double,Node*> p = evalFamily(exp.exps[i],familyEnvNode,scaffold,omegaDB,isDefinite);
      weight += p.first;
      operandNodes.push_back(p.second);
    }

    addApplicationEdges(operatorNode,operandNodes,requestNode,outputNode);
    weight += apply(requestNode,outputNode,scaffold,false,omegaDB);
    break;
  }
  }
  return {weight,node};
}

double Trace::apply(Node * requestNode,
		    Node * outputNode,
		    Scaffold & scaffold,
		    bool shouldRestore,
		    OmegaDB & omegaDB)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,shouldRestore,omegaDB);
  
  if (requestNode->getValue())
  {
    /* Regenerate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(requestNode->getValue());
    for (ESR esr : requests->esrs)
    {
      Node * esrParent = requestNode->sp()->findFamily(esr.id,requestNode->spaux());
      assert(esrParent);
      weight += regenInternal(esrParent,scaffold,shouldRestore,omegaDB);
    }
  }

  requestNode->isActive = true;
  
  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,shouldRestore,omegaDB);
  outputNode->isActive = true;
  return weight;
}
