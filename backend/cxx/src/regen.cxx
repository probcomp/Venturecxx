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
#include "address.h"

#include <cmath>

#include <iostream>
#include <typeinfo>
#include "sps/mem.h"

double Trace::regen(const vector<Node *> & border,
		    Scaffold * scaffold,
		    map<Node *,vector<double> > *gradients)
{
//  cout << "REGEN" << endl;
  assert(scaffold);
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold->isAbsorbing(node)) { weight += absorb(node,scaffold,gradients); }
    else /* Terminal resampling */
    {
      weight += regenInternal(node,scaffold,gradients);
      if (node->isObservation()) 
      { weight += constrain(node,node->observedValue, !shouldRestore); }
    }
  }
  return weight;
}

double Trace::regenParents(Node * node,
			   Scaffold * scaffold,
			   map<Node *,vector<double> > *gradients)
{
  assert(scaffold);

  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  { return regenInternal(node->lookedUpNode,scaffold,gradients); }

  double weight = 0;

  weight += regenInternal(node->operatorNode,scaffold,gradients);
  for (Node * operandNode : node->operandNodes)
  { weight += regenInternal(operandNode,scaffold,gradients); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += regenInternal(node->requestNode,scaffold,gradients);
    for (Node * esrParent : getESRParents(node))
    { weight += regenInternal(esrParent,scaffold,gradients); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold * scaffold,
		     map<Node *,vector<double> > *gradients)
{
  preAbsorb(node);
  assert(scaffold);
  double weight = 0;
  weight += regenParents(node,scaffold,gradients);
  weight += getSP(node)->logDensity(getValue(node),getArgs(node));
  getSP(node)->incorporate(getValue(node),getArgs(node));
  return weight;
}

double Trace::constrain(Node * node, VentureValue * value, bool reclaimValue)
{
  if (isReference(node)) { return constrain(getSourceNode(node),value,reclaimValue); }
  else
  {
//    cout << "constrain @ " << node->address << endl;
    /* New restriction, to ensure that we did not propose to an
       observation node with a non-trivial kernel. TODO handle
       this in loadDefaultKernels instead. */
    assert(getSP(node)->isRandomOutput);
    assert(getSP(node)->canAbsorbOutput); // TODO temporary
    preConstrain(node);
    getSP(node)->removeOutput(getValue(node),getArgs(node));

    if (reclaimValue) { getSP(node)->flushOutput(getValue(node)); }

    /* TODO need to set this on restore, based on the FlushQueue */

    double weight = getSP(node)->logDensityOutput(value,getArgs(node));
    setValue(node,value);
    setConstrained(node);
    clearNodeOwnsValue(node);
    getSP(node)->incorporateOutput(value,getArgs(node));
    if (getSP(node)->isRandomOutput) { constrainChoice(node); }
    return weight;
  }
}


double Trace::regenInternal(Node * node,
			    Scaffold * scaffold,
			    map<Node *,vector<double> > *gradients)
{
  if (!scaffold) { return 0; }
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    if (getRegenCount(node,scaffold) == 0)
    {
      weight += regenParents(node,scaffold,gradients);
      if (node->nodeType == NodeType::LOOKUP)
      { registerReference(node,node->lookedUpNode); }
      else /* Application node */
      { weight += applyPSP(node,scaffold,gradients); }
    }
    incrementRegenCount(node,scaffold);
  }
  return weight;
}

void Trace::processMadeSP(Node * node, bool isAAA)
{
  callCounts[{"processMadeSP",false}]++;
  cout << "processMadeSP @ " << node->address << endl;
  VentureSP * vsp = dynamic_cast<VentureSP *>(getValue(node));
  assert(vsp);
  if (vsp->makerNode) { return; }

  callCounts[{"processMadeSPfull",false}]++;

  SP * madeSP = vsp->sp;
  setVSPMakerNode(vsp,node);
  if (!isAAA)
  {
    if (madeSP->hasAux()) 
    { 
      regenMadeSPAux(node,madeSP); 
    }
    if (madeSP->hasAEKernel) { registerAEKernel(vsp); }
  }
}


double Trace::applyPSP(Node * node,
		       Scaffold * scaffold,
		       map<Node *,vector<double> > *gradients)
{
  callCounts[{"applyPSP",false}]++;
  cout << "applyPSP @ " << node->address << endl;

  SP * sp = getSP(node);
  preApplyPSP(node);
  assert(node->isValid());
  assert(sp->isValid());

  /* Almost nothing needs to be done if this node is a ESRReference.*/
  if (node->nodeType == NodeType::OUTPUT && sp->isESRReference)
  {
    if (getESRParents(node).empty()) { cout << "EMPTY: " << node << endl; }
    assert(!getESRParents(node).empty());
    registerReference(node,getESRParents(node)[0]);
    return 0;
  }
  if (node->nodeType == NodeType::REQUEST && sp->isNullRequest())
  {
    return 0;
  }

  assert(!isReference(node));

  /* Otherwise we need to actually do things. */

  double weight = 0;

  VentureValue * newValue;

  if (shouldRestore)
  {
    assert(omegaDB);
    if (scaffold && scaffold->isResampling(node)) { newValue = omegaDB->drgDB[node]; }
    else 
    { 
      newValue = getValue(node); 
      if (!newValue)
      {
	assert(newValue);
      }
    }
      
    /* If the kernel was an HSR kernel, then we restore all latents.
       TODO this could be made clearer. */
    if (sp->makesHSRs && scaffold && scaffold->isAAA(node))
    {
      sp->restoreAllLatents(getSPAux(node),omegaDB->latentDBs[getSP(node)]);
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
    if (omegaDB && omegaDB->latentDBs.count(getSP(node))) { latentDB = omegaDB->latentDBs[getSP(node)]; }

    newValue = k->simulate(oldValue,getArgs(node),latentDB,rng);
    weight += k->weight(newValue,oldValue,getArgs(node),latentDB);
    assert(isfinite(weight));

    VariationalLKernel * vlk = dynamic_cast<VariationalLKernel*>(k);
    if (vlk && gradients)
    {
      gradients->insert({node,vlk->gradientOfLogDensity(newValue,getArgs(node))});
    }
  }
  else
  {
    newValue = sp->simulate(getArgs(node),rng);
  }
  if (!newValue)
  {
    cout << "applyPSP: newValue = null" << endl;
    cout << "shouldRestore: " << shouldRestore << endl;
  }
  assert(newValue);
  assert(newValue->isValid());
  setValue(node,newValue);

  sp->incorporate(newValue,getArgs(node));

  if (dynamic_cast<VentureSP *>(getValue(node)))
  { processMadeSP(node,scaffold && scaffold->isAAA(node)); }
  if (sp->isRandom(node->nodeType)) { registerRandomChoice(node); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,gradients); }


  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   map<Node *,vector<double> > *gradients)
{
  /* Null request does not bother malloc-ing */
  if (!getValue(node)) { return 0; }
  preEvalRequests(node);
  double weight = 0;

  VentureRequest * requests = dynamic_cast<VentureRequest *>(getValue(node));
  assert(requests);

    /* First evaluate ESRs. */
  for (ESR esr : requests->esrs)
  {
//    cout << "evalRequest @ " << node->address << "..." ;
    assert(getSPAux(node)->isValid());
    Node * esrParent;
    if (!getSPAux(node)->families.count(esr.id))
    {
//      cout << "not found @ ";
      if (shouldRestore && omegaDB && omegaDB->spFamilyDBs.count({getVSP(node)->makerNode, esr.id}))
      {
	esrParent = omegaDB->spFamilyDBs[{getVSP(node)->makerNode, esr.id}];
	assert(esrParent);
	restoreSPFamily(getVSP(node),esr.id,esrParent,scaffold);
      }
      else
      {
	pair<double,Node*> p = evalFamily(Address(getSP(node),esr.id,"root"),esr.exp,esr.env,scaffold,false,gradients);      
	weight += p.first;
	esrParent = p.second;
      }
      getSP(node)->registerFamily(esr.id, esrParent, getSPAux(node));
    }
    else
    {
//      cout << "found @ ";
      esrParent = getSPAux(node)->families[esr.id];
      assert(esrParent->isValid());

      // right now only MSP's share
      // (guard against hash collisions)
      assert(dynamic_cast<MSP*>(getSP(node)));
      
    }
//    cout << esrParent->address << endl;
    addESREdge(esrParent,node->outputNode);
  }

  /* Next evaluate HSRs. */
  for (HSR * hsr : requests->hsrs)
  {
    LatentDB * latentDB = nullptr;
    if (omegaDB && omegaDB->latentDBs.count(getSP(node))) 
    { latentDB = omegaDB->latentDBs[getSP(node)]; }
    assert(!shouldRestore || latentDB);
    weight += getSP(node)->simulateLatents(getSPAux(node),hsr,shouldRestore,latentDB,rng);
  }

  return weight;
}

pair<double, Node*> Trace::evalVentureFamily(size_t directiveID, 
					     VentureValue * exp,		     
					     map<Node *,vector<double> > *gradients)
{
  return evalFamily(Address(nullptr,directiveID,"root"),exp,globalEnv,nullptr,true,gradients);
}

double Trace::restoreSPFamily(VentureSP * vsp,
			      size_t id,
			      Node * root,
			      Scaffold * scaffold)
{
  Node * makerNode = vsp->makerNode;
  if (omegaDB->spOwnedValues.count(make_pair(makerNode,id)))
  {
    makerNode->madeSPAux->ownedValues[id] = omegaDB->spOwnedValues[make_pair(makerNode,id)];
  }
  return restoreFamily(root,scaffold);
}


double Trace::restoreVentureFamily(Node * root)
{
  restoreFamily(root,nullptr);
  return 0;
}

double Trace::restoreFamily(Node * node,
			    Scaffold * scaffold)
{
  assert(node);
  if (node->nodeType == NodeType::VALUE)
  {
    // do nothing
  }
  else if (node->nodeType == NodeType::LOOKUP)
  {
    regenInternal(node->lookedUpNode,scaffold,nullptr);
    reconnectLookup(node);
  }
  else
  {
    assert(node->operatorNode);
    restoreFamily(node->operatorNode,scaffold);
    for (Node * operandNode : node->operandNodes)
    { restoreFamily(operandNode,scaffold); }
    apply(node->requestNode,node,scaffold,nullptr);
  }
  return 0;
}


pair<double,Node*> Trace::evalFamily(Address addr,
				     VentureValue * exp, 
				     VentureEnvironment * env,
				     Scaffold * scaffold,
				     bool isDefinite,
				     map<Node *,vector<double> > *gradients)
{
//  cout << "eval: " << addr << endl;
  double weight = 0;
  Node * node = nullptr;
  assert(exp);
  if (dynamic_cast<VenturePair*>(exp))
  {
    VentureList * list = dynamic_cast<VentureList*>(exp);
    VentureSymbol * car = dynamic_cast<VentureSymbol*>(listRef(list,0));
 
    if (car && car->sym == "quote")
    {
      node = new Node(addr,NodeType::VALUE, nullptr);
      setValue(node,listRef(list,1));
    }
    /* Application */
    else
    {
      Node * requestNode = new Node(addr.add("#req"),NodeType::REQUEST,nullptr,env);
      Node * outputNode = new Node(addr,NodeType::OUTPUT,nullptr,env);
      node = outputNode;

      Node * operatorNode;
      vector<Node *> operandNodes;
    
      pair<double,Node*> p = evalFamily(addr.add("#op"),listRef(list,0),env,scaffold,isDefinite,gradients);
      weight += p.first;
      operatorNode = p.second;
      
      for (uint8_t i = 1; i < listLength(list); ++i)
      {
	pair<double,Node*> p = evalFamily(addr.add("#arg" + to_string(i)),listRef(list,i),env,scaffold,isDefinite,gradients);
	weight += p.first;
	operandNodes.push_back(p.second);
      }

      addApplicationEdges(operatorNode,operandNodes,requestNode,outputNode);
      weight += apply(requestNode,outputNode,scaffold,gradients);
    }
  }
  /* Variable lookup */
  else if (dynamic_cast<VentureSymbol*>(exp))
  {
    VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(exp);
    Node * lookedUpNode = env->findSymbol(vsym);
    assert(lookedUpNode);
    weight += regenInternal(lookedUpNode,scaffold,gradients);

    node = new Node(addr,NodeType::LOOKUP,nullptr);
    connectLookup(node,lookedUpNode);
    registerReference(node,lookedUpNode);
  }
  /* Self-evaluating */
  else
  {
    node = new Node(addr,NodeType::VALUE,exp);
  }
  assert(node);
  return {weight,node};
}

double Trace::apply(Node * requestNode,
		    Node * outputNode,
		    Scaffold * scaffold,
		    map<Node *,vector<double> > *gradients)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,gradients);
  
  if (getValue(requestNode))
  {
    /* Regenerate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(getValue(requestNode));
    for (ESR esr : requests->esrs)
    {
      Node * esrParent = getSP(requestNode)->findFamily(esr.id,getSPAux(requestNode));
      assert(esrParent);
      assert(esrParent->isValid());
      weight += regenInternal(esrParent,scaffold,gradients);
    }
  }

  
  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,gradients);
  return weight;
}
