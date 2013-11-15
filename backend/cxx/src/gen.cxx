#include "node.h"
#include "value.h"
#include "env.h"
#include "sp.h"
#include "trace.h"
#include "scaffold.h"
#include "srs.h"
#include "flush.h"
#include "lkernel.h"
#include "utils.h"
#include <cmath>

#include <iostream>
#include <typeinfo>
#include "sps/mem.h"

double Trace::generate(const vector<Node *> & border,
		       Scaffold * scaffold,
		       Particle * xi)
{
  assert(scaffold);
  double weight = 0;
  for (Node * node : border)
  {
    if (scaffold->isAbsorbing(node)) { weight += absorb(node,scaffold,xi); }
    else
    {
      weight += generateInternal(node,scaffold,xi);
      if (node->isObservation()) { weight += constrain(node,node->observedValue,xi); }
    }
  }
  return weight;
}

double Trace::generateParents(Node * node,
			      Scaffold * scaffold,
			      Particle * xi)
{
  assert(scaffold);
  assert(node->nodeType != NodeType::VALUE);

  if (node->nodeType == NodeType::LOOKUP)
  // looked up node will be accurate, source node will not be
  { return generateInternal(node->lookedUpNode,scaffold,xi); }

  double weight = 0;

  weight += generateInternal(node->operatorNode,scaffold,xi);
  for (Node * operandNode : node->operandNodes)
  { weight += generateInternal(operandNode,scaffold,xi); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += generateInternal(node->requestNode,scaffold,xi);
    // ESR parents are owned by XI
    for (Node * esrParent : xi->ersParents[node])
    { weight += generateInternal(esrParent,scaffold,xi); }
  }
   
  return weight;
}


double Trace::absorb(Node * node,
		     Scaffold * scaffold,
		     Particle * xi)
{
  assert(scaffold);
  double weight = 0;
  weight += generateParents(node,scaffold,xi);
  xi->maybeCloneSPAux(node);
  Args args = xi->makeArgs(node);
  weight += xi->sp(node)->logDensity(node->value,args);
  xi->sp(node)->incorporate(node->value,args);
  return weight;
}

double Trace::constrain(Node * node, VentureValue * value, Particle * xi)
{
  if (xi->isReference(node)) { return constrain(xi->getSourceNode(node),value,xi); }
  else
  {
    assert(xi->sp(node)->isRandomOutput);
    assert(xi->sp(node)->canAbsorbOutput);

    xi->maybeCloneSPAux(node);
    Args args = xi->makeArgs(node);
    xi->sp(node)->removeOutput(xi->getValue(node),args);
    assert(xi->hasValueFor(node)); 

    if (reclaimValue) { xi->sp(node)->flushValue(xi->getValue(node),node->nodeType); }

    double weight = xi->sp(node)->logDensityOutput(value,args);
    xi->sp(node)->incorporateOutput(value,args);

    if (xi->sp(node)->isRandomOutput) 
    { 
      xi->unregisterRandomChoice(node); 
      xi->registerConstrainedChoice(node);
    }

    xi->setValue(node,value);

    return weight;
  }
}


double Trace::generateInternal(Node * node,
			       Scaffold * scaffold,
			       Particle * xi)
{
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    if (!xi->hasValueFor(node))
    {
      weight += generateParents(node,scaffold,xi);
      if (node->nodeType == NodeType::LOOKUP)
      { 
	// copies the value in, why not
	xi->registerReference(node,node->lookedUpNode);
      }
      else /* Application node */
      { weight += applyPSP(node,scaffold,xi); }
    }
  }
  else if (scaffold->hasAAANodes)
  {
    if (xi->isReference(node) && scaffold->isAAA(xi->getSourceNode(node)))
    { weight += generateInternal(xi->getSourceNode(node),scaffold,xi); }
  }
  return weight;
}

void Trace::processMadeSP(Node * node, bool isAAA, Particle * xi)
{
  callCounts[{"processMadeSP",false}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(xi->getValue(node));
  if (vsp->makerNode) { return; }

  xi->maybeCloneMadeSPAux(node);

  callCounts[{"processMadeSPfull",false}]++;

  assert(vsp);

  SP * madeSP = vsp->sp;
  vsp->makerNode = node;
  if (!isAAA && madeSP->hasAux())
  {
    xi->registerSPAux(node,madeSP->constructSPAux());
  }
}


double Trace::applyPSP(Node * node,
		       Scaffold * scaffold,
		       Particle * xi)
{
  callCounts[{"applyPSP",false}]++;
  SP * sp = xi->sp(node);
  assert(node->isValid());
  assert(sp->isValid());

  /* Almost nothing needs to be done if this node is a ESRReference.*/
  if (node->nodeType == NodeType::OUTPUT && sp->isESRReference)
  {
    assert(!node->esrParents.empty());
    xi->registerReference(node,xi->esrParents[node][0]);
    return 0;
  }
  if (node->nodeType == NodeType::REQUEST && xi->sp(node)->isNullRequest())
  {
    return 0;
  }

  assert(!xi->isReference(node));

  /* Otherwise we need to actually do things. */
  double weight = 0;

  VentureValue * newValue;
  xi->maybeCloneSPAux(node);
  Args args = xi->makeArgs(node);

  if (scaffold->hasKernelFor(node))
  {
    VentureValue * oldValue = nullptr;
    LKernel * k = scaffold->lkernels[node];

    newValue = k->simulate(oldValue,args,rng);
    weight += k->weight(newValue,args);
    assert(isfinite(weight));
  }
  else
  {
    newValue = sp->simulate(args,rng);
  }
  assert(newValue);
  assert(newValue->isValid());

  xi->setValue(node,newValue);
  sp->incorporate(newValue,args);

  if (dynamic_cast<VentureSP *>(newValue)) { processMadeSP(node,scaffold->isAAA(node),xi); }
  if (node->sp()->isRandom(node->nodeType)) { xi->registerRandomChoice(node); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,xi); }

  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   Particle * xi)
{
  /* Null request does not bother malloc-ing */
  if (!xi->getValue(node)) { return 0; }
  double weight = 0;

  VentureRequest * requests = dynamic_cast<VentureRequest *>(xi->getValue(node));
  assert(xi->getSPAux(node));
  SPAux * spaux = xi->getSPAux(node);

  /* First evaluate ESRs. */
  for (ESR esr : requests->esrs)
  {
    assert(spaux->isValid());
    if (!spaux->families.count(esr.id))
    {
      pair<double,Node*> p = evalFamily(esr.exp,esr.env,scaffold,xi);      
      weight += p.first;
      spaux->families[esr.id] = p.second;
    }
    else 
    { 
      assert(spaux->families[esr.id]->isValid());
      assert(dynamic_cast<MSP*>(xi->sp(node))); 
    }
    xi->esrParents[node->outputNode].push_back(spaux->families[esr.id]);
  }

  for (HSR * hsr : requests->hsrs)
  {
    weight += xi->sp(node)->simulateLatents(spaux,hsr,rng);
  }

  return weight;
}

pair<double,Node*> Trace::evalFamily(VentureValue * exp, 
				     VentureEnvironment * env,
				     Scaffold * scaffold,
				     Particle * xi)
{
  double weight = 0;
  Node * node = nullptr;
  assert(exp);
  if (dynamic_cast<VenturePair*>(exp))
  {
    VentureList * list = dynamic_cast<VentureList*>(exp);
    VentureSymbol * car = dynamic_cast<VentureSymbol*>(listRef(list,0));
 
    if (car && car->sym == "quote")
    {
      node = new Node(NodeType::VALUE);
      xi->setValue(node,listRef(list,1));
    }
    /* Application */
    else
    {
      Node * requestNode = new Node(NodeType::REQUEST);
      Node * outputNode = new Node(NodeType::OUTPUT);
      node = outputNode;

      Node * operatorNode;
      vector<Node *> operandNodes;
    
      pair<double,Node*> p = evalFamily(listRef(list,0),env,scaffold,xi);
      weight += p.first;
      operatorNode = p.second;
      
      for (uint8_t i = 1; i < listLength(list); ++i)
      {
	pair<double,Node*> p = evalFamily(listRef(list,i),env,scaffold,xi);
	weight += p.first;
	operandNodes.push_back(p.second);
      }

      addApplicationEdges(operatorNode,operandNodes,requestNode,outputNode);
      weight += apply(requestNode,outputNode,scaffold,xi);
    }
  }
  /* Variable lookup */
  else if (dynamic_cast<VentureSymbol*>(exp))
  {
    VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(exp);
    Node * lookedUpNode = env->findSymbol(vsym);
    assert(lookedUpNode);
    weight += generateInternal(lookedUpNode,scaffold,xi);
    node = new Node(NodeType::LOOKUP);
    node->lookedUpNode = lookedUpNode;
    xi->registerReference(node,lookedUpNode);
  }
  /* Self-evaluating */
  else
  {
    node = new Node(NodeType::VALUE);
    xi->setValue(node, exp);
  }
  assert(node);
  return {weight,node};
}

double Trace::apply(Node * requestNode,
		    Node * outputNode,
		    Scaffold * scaffold,
		    Particle * xi)
{
  double weight = 0;

  /* Call the requester PSP. */
  weight += applyPSP(requestNode,scaffold,xi);
  
  SPAux * spaux = xi->getSPAux(requestNode);

  if (xi->getValue(requestNode))
  {
    /* Generate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(xi->getValue(requestNode));
    for (ESR esr : requests->esrs)
    {
      Node * esrParent = spaux->families[esr.id];
      assert(esrParent);
      weight += generateInternal(esrParent,scaffold,xi);
    }
  }

  /* Call the output PSP. */
  weight += applyPSP(outputNode,scaffold,xi);
  return weight;
}
