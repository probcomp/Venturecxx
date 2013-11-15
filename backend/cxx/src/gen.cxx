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
      if (node->isObservation()) { weight += constrain(node,node->observedValue,!shouldRestore,xi); }
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
  { return generateInternal(node->lookedUpNode,scaffold,xi); }

  double weight = 0;

  weight += generateInternal(node->operatorNode,scaffold,xi);
  for (Node * operandNode : node->operandNodes)
  { weight += generateInternal(operandNode,scaffold,xi); }
  
  if (node->nodeType == NodeType::OUTPUT)
  {
    weight += generateInternal(node->requestNode,scaffold,xi);
    for (Node * esrParent : node->esrParents)
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
  Args args = xi->makeArgs(node);
  weight += xi->sp(node)->logDensity(node->value,args);
  xi->sp(node)->incorporate(node->value,args);
  return weight;
}

double Trace::constrain(Node * node, VentureValue * value, bool reclaimValue, Particle * xi)
{
  if (node->isReference()) { return constrain(node->sourceNode,value,reclaimValue,xi); }
  else
  {
    assert(xi->sp(node)->isRandomOutput);
    assert(xi->sp(node)->canAbsorbOutput);
    assert(!scaffold || !scaffold->isResampling(node->operatorNode)); // TODO temporary

    Args args = xi->makeArgs(node);
    xi->sp(node)->removeOutput(xi->values[node],args);
    if (xi) { assert(xi->values.count(node)); xi->values[node] = value; }

    if (reclaimValue) { xi->sp(node)->flushValue(xi->values[node],node->nodeType); }

    double weight = xi->sp(node)->logDensityOutput(value,args);
    xi->sp(node)->incorporateOutput(value,args);
    return weight;
  }
}


double Trace::generateInternal(Node * node,
			       Scaffold * scaffold,
			       Particle * xi)
{
  if (!scaffold) { return 0; }
  double weight = 0;

  if (scaffold->isResampling(node))
  {
    Scaffold::DRGNode &drgNode = scaffold->drg[node];
    if (drgNode.generateCount == 0)
    {
      weight += generateParents(node,scaffold,xi);
      if (node->nodeType == NodeType::LOOKUP)
      { xi->values[node] = xi->values[node->lookedUpNode]->value; }
      else /* Application node */
      { weight += applyPSP(node,scaffold,xi); }
    }
    drgNode.generateCount++;
  }
  else if (scaffold->hasAAANodes)
  {
    if (node->isReference() && scaffold->isAAA(node->sourceNode))
    { weight += generateInternal(node->sourceNode,scaffold,xi); }
  }
  return weight;
}

void Trace::processMadeSP(Node * node, bool isAAA, Particle * xi)
{
  callCounts[{"processMadeSP",false}]++;

  VentureSP * vsp = dynamic_cast<VentureSP *>(xi->values[node]);
  if (vsp->makerNode) { return; }

  callCounts[{"processMadeSPfull",false}]++;

  assert(vsp);

  SP * madeSP = vsp->sp;
  vsp->makerNode = node;
  if (!isAAA && madeSP->hasAux())
  {
    // Note we do not set this in the actual node, only in the particle */
    xi->spauxs[node] = madeSP->constructSPAux();
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
    node->registerReference(node->esrParents[0]);
    


    }
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
  xi->values[node] = newValue;

  sp->incorporate(newValue,args);

  if (dynamic_cast<VentureSP *>(newValue))
  { processMadeSP(node,scaffold->isAAA(node),xi); }
  if (node->nodeType == NodeType::REQUEST) { evalRequests(node,scaffold,xi); }

  return weight;
}

double Trace::evalRequests(Node * node,
			   Scaffold * scaffold,
			   Particle * xi)
{
  /* Null request does not bother malloc-ing */
  if (!xi->values[node]) { return 0; }
  double weight = 0;

  VentureRequest * requests = dynamic_cast<VentureRequest *>(xi->values[node]);
  SPAux * spaux = xi->getSPAuxForNode(node);

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
      xi->values[node] = listRef(list,1);
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
    node->registerReference(lookedUpNode);
    assert(lookedUpNode);
    weight += generateInternal(lookedUpNode,scaffold,xi);
    // Note: does not actually add the edges
    node = new Node(NodeType::LOOKUP);
    xi->values[node] = lookedUpNode->value;
  }
  /* Self-evaluating */
  else
  {
    node = new Node(NodeType::VALUE);
    xi->values[node] = exp;
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
  
  SPAux * spaux = xi->getSPAuxForNode(requestNode);

  if (xi->values[requestNode])
  {
    /* Generate any ESR nodes requested. */
    VentureRequest * requests = dynamic_cast<VentureRequest *>(xi->values[requestNode]);
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
