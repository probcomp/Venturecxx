#include "detach.h"
#include "node.h"
#include "trace.h"
#include "scaffold.h"
#include "lkernel.h"
#include "db.h"
#include "sp.h"
#include "psp.h"

#include <iostream>

using std::cout;
using std::endl;

pair<double,shared_ptr<DB> > detachAndExtract(Trace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold)
{
  double weight = 0;
  shared_ptr<DB> db(new DB());
  for (vector<Node*>::const_reverse_iterator borderIter = border.rbegin();
       borderIter != border.rend();
       ++borderIter)
  {
    Node * node = *borderIter;
    if (scaffold->isAbsorbing(node)) 
    {
      ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
      assert(appNode);
      weight += detach(trace,appNode,scaffold,db);
    }
    else
    {
      if (trace->isObservation(node))
      {
	weight += unconstrain(trace,trace->getOutermostNonRefAppNode(node)); 
      }
      weight += extract(trace,node,scaffold,db);
    }
  }
  return make_pair(weight,db);
}


double unconstrain(Trace * trace,OutputNode * node)
{
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr value = trace->getValue(node);

  trace->unregisterConstrainedChoice(node);
  psp->unincorporate(value,args);
  double weight = psp->logDensity(value,args);
  psp->incorporate(value,args);
  return weight;
}

double detach(Trace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  // cout << "detach(" << node << ")" << endl;
  
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);

  psp->unincorporate(groundValue,args);
  double weight = psp->logDensity(groundValue,args);
  weight += extractParents(trace,node,scaffold,db);
  return weight;
}


double extractParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = extractESRParents(trace,node,scaffold,db);
  for (vector<Node*>::reverse_iterator defParentIter = node->definiteParents.rbegin();
       defParentIter != node->definiteParents.rend();
       ++defParentIter)
  {
    weight += extract(trace,*defParentIter,scaffold,db);
  }
  return weight;
}

double extractESRParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = 0;
  vector<RootOfFamily> esrParents = trace->getESRParents(node);
  for (vector<RootOfFamily>::reverse_iterator esrParentIter = esrParents.rbegin();
       esrParentIter != esrParents.rend();
       ++esrParentIter)
  {
    weight += extract(trace,esrParentIter->get(),scaffold,db);
  }
  return weight;
}

double extract(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  // cout << "extractOuter(" << node << ")" << endl;
  double weight = 0;
  VentureValuePtr value = trace->getValue(node);

  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  if (spRef && spRef->makerNode != node && scaffold->isAAA(spRef->makerNode))
  {
    weight += extract(trace,spRef->makerNode,scaffold,db);
  }

  if (scaffold->isResampling(node))
  {
    // cout << "extract(" << node << ") = " << trace->getRegenCount(scaffold,node) << endl;
    trace->decRegenCount(scaffold,node);
    assert(trace->getRegenCount(scaffold,node) >= 0);
    if (trace->getRegenCount(scaffold,node) == 0)
    {
      LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
      RequestNode * requestNode = dynamic_cast<RequestNode*>(node);
      OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
      if (lookupNode) { trace->setValue(lookupNode,shared_ptr<VentureValue>()); }
      else if (requestNode) 
      { 
        weight += unevalRequests(trace,requestNode,scaffold,db);
        weight += unapplyPSP(trace,requestNode,scaffold,db);
      }
      else
      {
	assert(outputNode);
        weight += unapplyPSP(trace,outputNode,scaffold,db);
      }
      weight += extractParents(trace,node,scaffold,db);
    }
  }
  return weight;
}

double unevalFamily(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = 0;

  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode) { }
  else if (lookupNode)
  {
    trace->disconnectLookup(lookupNode);
    trace->setValue(lookupNode,shared_ptr<VentureValue>());
    weight += extractParents(trace,lookupNode,scaffold,db);
  }
  else
  {
    assert(outputNode);
    weight += unapply(trace,outputNode,scaffold,db);
    for (vector<Node*>::reverse_iterator operandNodeIter = outputNode->operandNodes.rbegin();
	 operandNodeIter != outputNode->operandNodes.rend();
	 ++operandNodeIter)
    {
      weight += unevalFamily(trace,*operandNodeIter,scaffold,db);
    }
    weight += unevalFamily(trace,outputNode->operatorNode,scaffold,db);
  }
  return weight;
}

double unapply(Trace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = unapplyPSP(trace,node,scaffold,db);
  weight += extractESRParents(trace,node,scaffold,db);
  weight += unevalRequests(trace,node->requestNode,scaffold,db);
  weight += unapplyPSP(trace,node->requestNode,scaffold,db);
  return weight;
}

void teardownMadeSP(Trace * trace,Node * makerNode,bool isAAA,shared_ptr<DB> db)
{
  shared_ptr<VentureSP> sp = trace->getMadeSP(makerNode);
  assert(sp);
  if (!isAAA)
  {
    if (sp->hasAEKernel()) { trace->unregisterAEKernel(makerNode); }
    db->registerMadeSPAux(makerNode,trace->getMadeSPAux(makerNode));
    trace->destroyMadeSPRecord(makerNode);
  }
  else
  {
    trace->setMadeSP(makerNode,shared_ptr<VentureSP>());
  }
  trace->setValue(makerNode,sp);
}

double unapplyPSP(Trace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  // cout << "unapplyPSP(" << node << ")" << endl;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);


  // TODO ScopeInclude
  if (psp->isRandom()) { trace->unregisterUnconstrainedChoice(node); }
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(node));
  if (spRef && spRef->makerNode == node) { teardownMadeSP(trace,node,scaffold->isAAA(node),db); }

  VentureValuePtr value = trace->getValue(node);

  double weight = 0;
  psp->unincorporate(value,args);
  if (scaffold->hasLKernel(node)) { weight += scaffold->getLKernel(node)->reverseWeight(trace,value,args); }
  db->registerValue(node,value);

  trace->setValue(node,shared_ptr<VentureValue>());

  return weight;
}


double unevalRequests(Trace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = 0;
  const vector<ESR>& esrs = trace->getValue(node)->getESRs();
  //const vector<shared_ptr<LSR> >& lsrs = trace->getValue(node)->getLSRs();
  
  // TODO Latents

  for (vector<ESR>::const_reverse_iterator esrIter = esrs.rbegin();
       esrIter != esrs.rend();
       ++esrIter)
  {
    RootOfFamily esrRoot = trace->popLastESRParent(node->outputNode);
    if (trace->getNumRequests(esrRoot))
    {
      trace->unregisterMadeSPFamily(trace->getOperatorSPMakerNode(node),esrIter->id);
      db->registerSPFamily(trace->getMadeSP(trace->getOperatorSPMakerNode(node)),esrIter->id,esrRoot);
      weight += unevalFamily(trace,esrRoot.get(),scaffold,db);
    }
  }
  return weight;
}
