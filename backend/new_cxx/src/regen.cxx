#include "regen.h"

#include "scaffold.h"
#include "trace.h"
#include "node.h"
#include "expressions.h"
#include "env.h"
#include "sp.h"
#include "db.h"
#include "psp.h"
#include "lkernel.h"

#include <iostream>

using std::cout;
using std::endl;

double regenAndAttach(Trace * trace,
		      const vector<Node*> & border,
		      shared_ptr<Scaffold> scaffold,
		      bool shouldRestore,
		      shared_ptr<DB> db,
		      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  map<Node*,VentureValuePtr> constraintsToPropagate;
  for (size_t i = 0; i < border.size(); ++i)
  {
    Node * node = border[i];
    if (scaffold->isAbsorbing(node))
    {
      ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
      assert(appNode);
      weight += attach(trace,appNode,scaffold,shouldRestore,db,gradients);
    }
    else
    {
      weight += regen(trace,node,scaffold,shouldRestore,db,gradients);
      if (trace->isObservation(node))
      {
        OutputNode * outputNode = trace->getOutermostNonRefAppNode(node);
	      weight += constrain(trace,outputNode,trace->getObservedValue(node));
        constraintsToPropagate[outputNode] = trace->getObservedValue(node);
      }
    }
  }
  // Propagate constraints
  for (map<Node*,VentureValuePtr>::iterator iter1 = constraintsToPropagate.begin();
       iter1 != constraintsToPropagate.end();
       ++iter1)
  {
    Node * node = iter1->first;
    set<Node*> children = trace->getChildren(node);
    for (set<Node*>::iterator iter2 = children.begin();
	 iter2 != children.end();
	 ++iter2)
    {
      propagateConstraint(trace,*iter2,iter1->second);
    }
  }
  return weight;
}


double constrain(Trace * trace,
		 OutputNode * node,
		 VentureValuePtr value)
{
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);

  psp->unincorporate(trace->getValue(node),args);
  double weight = psp->logDensity(value,args);
  trace->setValue(node,value);
  psp->incorporate(value,args);
  trace->registerConstrainedChoice(node);
  return weight;
}


void propagateConstraint(Trace * trace,
			 Node * node,
			 VentureValuePtr value)
{
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  RequestNode * requestNode = dynamic_cast<RequestNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
  if (lookupNode) { trace->setValue(lookupNode,value); }
  else if (requestNode)
  {
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(requestNode))->getPSP(requestNode);
    if (!dynamic_pointer_cast<NullRequestPSP>(psp)) { throw "Cannot make requests downstream of a node that gets constrained during regen"; }
  }
  else
  {
    assert(outputNode);
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
    if (psp->isRandom()) { throw "Cannot make random choices downstream of a node that gets constrained during regen"; }
    trace->setValue(node,psp->simulate(trace->getArgs(outputNode),trace->rng));
  }
  set<Node*> children = trace->getChildren(node);
  for (set<Node*>::iterator iter = children.begin();
       iter != children.end();
       ++iter)
  {
    propagateConstraint(trace,*iter,value);
  }
}


double attach(Trace * trace,
	      ApplicationNode * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = regenParents(trace,node,scaffold,shouldRestore,db,gradients);
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);
  weight += psp->logDensity(groundValue,args);
  psp->incorporate(groundValue,args);
  return weight;
}


double regen(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{ 
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    if (trace->getRegenCount(scaffold,node) == 0)
    {
      weight += regenParents(trace,node,scaffold,shouldRestore,db,gradients);
      LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
      RequestNode * requestNode = dynamic_cast<RequestNode*>(node);
      OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
      if (lookupNode) { trace->setValue(node, trace->getValue(lookupNode->sourceNode)); }
      else if (requestNode)
      {
        weight += applyPSP(trace,requestNode,scaffold,shouldRestore,db,gradients);
        weight += evalRequests(trace,requestNode,scaffold,shouldRestore,db,gradients);
      }
      else
      {
	assert(outputNode);
        weight += applyPSP(trace,outputNode,scaffold,shouldRestore,db,gradients);
      }
    }
    trace->incRegenCount(scaffold,node);
  }
  VentureValuePtr value = trace->getValue(node);
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  if (spRef && spRef->makerNode != node && scaffold->isAAA(spRef->makerNode))
  {
    weight += regen(trace,spRef->makerNode,scaffold,shouldRestore,db,gradients);
  }
  return weight;
}

double regenParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  for (size_t i = 0; i < node->definiteParents.size(); ++i) { weight += regen(trace,node->definiteParents[i],scaffold,shouldRestore,db,gradients); }
  return weight + regenESRParents(trace,node,scaffold,shouldRestore,db,gradients);
}

double regenESRParents(Trace * trace,
	      Node * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  vector<Node*> esrParents = trace->getESRParents(node);
  for (size_t i = 0; i < esrParents.size(); ++i) { weight += regen(trace,esrParents[i],scaffold,shouldRestore,db,gradients); }
  return weight;
}

pair<double,Node*> evalFamily(Trace * trace,
			      VentureValuePtr exp,
			      shared_ptr<VentureEnvironment> env,
			      shared_ptr<Scaffold> scaffold,
			      shared_ptr<DB> db,
			      shared_ptr<map<Node*,Gradient> > gradients)
{
  if (isVariable(exp))
  {
    cout << "isVariable" << endl;
    double weight = 0;
    shared_ptr<VentureSymbol> symbol = dynamic_pointer_cast<VentureSymbol>(exp);
    Node * sourceNode = env->lookupSymbol(symbol);
    weight = regen(trace,sourceNode,scaffold,false,db,gradients);

    /* DEBUG */
    shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(sourceNode));
    assert(spRef);
    /* END DEBUG */

    return make_pair(weight,trace->createLookupNode(sourceNode));
  }
  else if (isSelfEvaluating(exp)) { cout << "isSelfEvaluating" << endl; return make_pair(0,trace->createConstantNode(exp)); }
  else if (isQuotation(exp)) { return make_pair(0,trace->createConstantNode(textOfQuotation(exp))); }
  else
  {
    cout << "isApp" << endl;
    shared_ptr<VentureArray> array = dynamic_pointer_cast<VentureArray>(exp);
    pair<double,Node*> p = evalFamily(trace,array->xs[0],env,scaffold,db,gradients);
    double weight = p.first;
    Node * operatorNode = p.second;

    /* DEBUG */
    shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(operatorNode));
    assert(spRef);
    /* END DEBUG */

    vector<Node*> operandNodes;
    for (size_t i = 1; i < array->xs.size(); ++i)
    {
      pair<double,Node*>p = evalFamily(trace,array->xs[i],env,scaffold,db,gradients);
      weight += p.first;
      operandNodes.push_back(p.second);
    }

    pair<RequestNode*,OutputNode*> appNodes = trace->createApplicationNodes(operatorNode,operandNodes,env);
    weight += apply(trace,appNodes.first,appNodes.second,scaffold,false,db,gradients);
    return make_pair(weight,p.second);
  }
}

double apply(Trace * trace,
	      RequestNode * requestNode,
	     OutputNode * outputNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = applyPSP(trace,requestNode,scaffold,shouldRestore,db,gradients);
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,db,gradients);

  /* DEBUG */
  pair<vector<ESR>,vector<LSR *> > p = trace->getValue(requestNode)->getRequests();
  assert(trace->getESRParents(outputNode).size() == p.first.size());  
  /* END DEBUG */

  weight += regenESRParents(trace,outputNode,scaffold,shouldRestore,db,gradients);
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,db,gradients);
  return weight;
}



void processMadeSP(Trace * trace, Node * makerNode, bool isAAA)
{
  shared_ptr<VentureSP> sp = dynamic_pointer_cast<VentureSP>(trace->getValue(makerNode));
  if (!isAAA)
  {
    trace->initMadeSPRecord(makerNode,sp,sp->constructSPAux());
    if (sp->hasAEKernel()) { trace->registerAEKernel(makerNode); }
  }
  else { trace->setMadeSP(makerNode,sp); }
  trace->setValue(makerNode,shared_ptr<VentureValue>(new VentureSPRef(makerNode)));
}

double applyPSP(Trace * trace,
	      ApplicationNode * node,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);

  VentureValuePtr oldValue;
  VentureValuePtr newValue;

  if (db->hasValue(node)) { oldValue = db->getValue(node); }

  if (scaffold->hasLKernel(node))
  {
    shared_ptr<LKernel> k = scaffold->getLKernel(node);
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = k->simulate(trace,oldValue,args,trace->rng); }

    weight += k->weight(trace,newValue,oldValue,args);
    //TODO variational
  }
  else
  {
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = psp->simulate(args,trace->rng); } // TODO rng
  }

  trace->setValue(node,newValue);
  psp->incorporate(newValue,args);

  if (dynamic_pointer_cast<VentureSP>(newValue)) { processMadeSP(trace,node,scaffold->isAAA(node)); }
  /* TODO TEMP MILESTONE */
  // if (psp->isRandom()) { trace->registerRandomChoice(node); } 
  // if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  // {
  //   ScopeID scope = trace->getValue(node->operandNodes[0]);
  //   BlockID block = trace->getValue(node->operandNodes[1]);
  //   Node * blockNode = node->operandNodes[2];
  //   trace->registerRandomChoiceInScope(scope,block,blockNode);
  // }
  return weight;
}


double evalRequests(Trace * trace,
	      RequestNode * requestNode,
	      shared_ptr<Scaffold> scaffold,
	      bool shouldRestore,
	      shared_ptr<DB> db,
	      shared_ptr<map<Node*,Gradient> > gradients)
{
  double weight = 0;
  pair<vector<ESR>,vector<LSR *> > requests = trace->getValue(requestNode)->getRequests();

  for (size_t i = 0; i < requests.first.size(); ++i)
  {
    ESR esr = requests.first[i];
    if (!trace->containsMadeSPFamily(trace->getOperatorSPMakerNode(requestNode),esr.id))
    {
      RootOfFamily esrParent;
      if (shouldRestore)
      {
        esrParent = db->getESRParent(trace->getMadeSP(trace->getOperatorSPMakerNode(requestNode)),esr.id);
        weight += restore(trace,esrParent.get(),scaffold,db,gradients);
      }
      else
      {
      	pair<double,Node*> p = evalFamily(trace,esr.exp,esr.env,scaffold,db,gradients);
        weight += p.first;
	esrParent = shared_ptr<Node>(p.second);
      }
      trace->registerFamily(requestNode,esr.id,esrParent);
    }
    RootOfFamily esrParent = trace->getMadeSPFamilyRoot(trace->getOperatorSPMakerNode(requestNode),esr.id);
    trace->addESREdge(esrParent.get(),requestNode->outputNode);
  }

  // TODO LSRs
  return weight;
}



double restore(Trace * trace,
	       Node * node,
	       shared_ptr<Scaffold> scaffold,
	       shared_ptr<DB> db,
	       shared_ptr<map<Node*,Gradient> > gradients) 
{ assert(false); }
