#include "detach.h"
#include "node.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "lkernel.h"
#include "db.h"
#include "sp.h"
#include "psp.h"
#include "sps/scope.h"
#include <iostream>

#include <boost/foreach.hpp>

using std::cout;
using std::endl;

pair<double,shared_ptr<DB> > detachAndExtract(ConcreteTrace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold, bool compute_gradient)
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
      weight += detach(trace,appNode,scaffold,db, compute_gradient);
    }
    else
    {
      if (trace->isObservation(node))
      {
	      weight += unconstrain(trace,trace->getOutermostNonRefAppNode(node)); 
      }
      weight += extract(trace,node,scaffold,db, compute_gradient);
    }
  }
  return make_pair(weight,db);
}


double unconstrain(ConcreteTrace * trace,OutputNode * node)
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

double detach(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  // cout << "detach(" << node << ")" << endl;
  
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);

  psp->unincorporate(groundValue,args);
  double weight = psp->logDensity(groundValue,args);
  if(compute_gradient) {
    vector<shared_ptr<Node> > parents_esr = trace->getESRParents(node);
    vector<Node*> parents;
    BOOST_FOREACH(shared_ptr<Node> node, parents_esr) {
      parents.push_back(node.get());
    }
    parents.insert(parents.end(), args->operandNodes.begin(), args->operandNodes.end());
    pair<VentureValuePtr, vector<VentureValuePtr> > grad = psp->gradientOfLogDensity(groundValue, args);
    // cout << "detach partial 1: " << endl;
    // cout << psp->toString() << endl;
    // cout << "grad " << toString(grad.second) << endl;
    db->addPartials(parents, grad.second);
  }
  weight += extractParents(trace,node,scaffold,db, compute_gradient);
  return weight;
}


double extractParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  double weight = extractESRParents(trace,node,scaffold,db, compute_gradient);
  for (vector<Node*>::reverse_iterator defParentIter = node->definiteParents.rbegin();
       defParentIter != node->definiteParents.rend();
       ++defParentIter)
  {
    weight += extract(trace,*defParentIter,scaffold,db, compute_gradient);
  }
  return weight;
}

double extractESRParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  double weight = 0;
  vector<RootOfFamily> esrParents = trace->getESRParents(node);
  for (vector<RootOfFamily>::reverse_iterator esrParentIter = esrParents.rbegin();
       esrParentIter != esrParents.rend();
       ++esrParentIter)
  {
    weight += extract(trace,esrParentIter->get(),scaffold,db, compute_gradient);
  }
  return weight;
}

double extract(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  //cout << "extractOuter(" << node << ")" << endl;
  double weight = 0;
  VentureValuePtr value = trace->getValue(node);

  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  if (spRef && spRef->makerNode != node && scaffold->isAAA(spRef->makerNode))
  {
    weight += extract(trace,spRef->makerNode,scaffold,db, compute_gradient);
  }

  if (scaffold->isResampling(node))
  {
    //cout << "extract(" << node << ") = " << trace->getRegenCount(scaffold,node) << endl;
    trace->decRegenCount(scaffold,node);
    assert(trace->getRegenCount(scaffold,node) >= 0);
    if (trace->getRegenCount(scaffold,node) == 0)
    {
      LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
      RequestNode * requestNode = dynamic_cast<RequestNode*>(node);
      OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
      if (lookupNode) { 
        trace->clearValue(lookupNode); 
        if(compute_gradient) { // d/dx is 1 for a lookup node.
          BOOST_FOREACH(Node* p, node->definiteParents) {
            db->addPartial(p, db->getPartial(node));
          }
        }
      }
      else if (requestNode) 
      { 
        weight += unevalRequests(trace,requestNode,scaffold,db, compute_gradient);
        weight += unapplyPSP(trace,requestNode,scaffold,db, compute_gradient);
      }
      else
      {
	      assert(outputNode);
        weight += unapplyPSP(trace,outputNode,scaffold,db,compute_gradient);
      }
      weight += extractParents(trace,node,scaffold,db,compute_gradient);
    }
  }
  return weight;
}

double unevalFamily(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  //cout << "unevalFamily(" << node << ")" << endl;
  double weight = 0;

  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode) { }
  else if (lookupNode)
  {
    if(compute_gradient) {
      BOOST_FOREACH(Node* p, node->definiteParents) {
        db->addPartial(p, db->getPartial(node));
      }
    }
    trace->disconnectLookup(lookupNode);
    trace->clearValue(lookupNode);
    weight += extractParents(trace,lookupNode,scaffold,db, compute_gradient);
  }
  else
  {
    assert(outputNode);
    weight += unapply(trace,outputNode,scaffold,db, compute_gradient);
    for (vector<Node*>::reverse_iterator operandNodeIter = outputNode->operandNodes.rbegin();
	 operandNodeIter != outputNode->operandNodes.rend();
	 ++operandNodeIter)
    {
      weight += unevalFamily(trace,*operandNodeIter,scaffold,db, compute_gradient);
    }
    weight += unevalFamily(trace,outputNode->operatorNode,scaffold,db, compute_gradient);
  }
  return weight;
}

double unapply(ConcreteTrace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  double weight = unapplyPSP(trace,node,scaffold,db, compute_gradient);
  weight += extractESRParents(trace,node,scaffold,db, compute_gradient);
  weight += unevalRequests(trace,node->requestNode,scaffold,db, compute_gradient);
  weight += unapplyPSP(trace,node->requestNode,scaffold,db, compute_gradient);
  return weight;
}

void teardownMadeSP(ConcreteTrace * trace,Node * makerNode,bool isAAA,shared_ptr<DB> db)
{
  shared_ptr<VentureSPRecord> spRecord = trace->getMadeSPRecord(makerNode);
  assert(spRecord);
  trace->setValue(makerNode,spRecord);

  shared_ptr<SP> sp = spRecord->sp;
  if (sp->hasAEKernel()) { trace->unregisterAEKernel(makerNode); }
  db->registerMadeSPAux(makerNode,trace->getMadeSPAux(makerNode));
  if (isAAA) 
    {
      OutputNode * outputNode = dynamic_cast<OutputNode*>(makerNode);
      assert(outputNode);
      trace->registerAAAMadeSPAux(outputNode,trace->getMadeSPAux(outputNode));
    }
  trace->destroyMadeSPRecord(makerNode);
}

double unapplyPSP(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  //cout << "unapplyPSP(" << node << ")" << endl;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);


  // TODO ScopeInclude
  if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  {
    ScopeID scope = trace->getValue(node->operandNodes[0]);
    BlockID block = trace->getValue(node->operandNodes[1]);
    Node * blockNode = node->operandNodes[2];
    trace->unregisterUnconstrainedChoiceInScope(scope,block,blockNode);
  }

  if (psp->isRandom()) { trace->unregisterUnconstrainedChoice(node); }
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(node));
  if (spRef && spRef->makerNode == node) { teardownMadeSP(trace,node,scaffold->isAAA(node),db); }

  VentureValuePtr value = trace->getValue(node);

  double weight = 0;
  psp->unincorporate(value,args);
  if (scaffold->hasLKernel(node)) { 
    weight += scaffold->getLKernel(node)->reverseWeight(trace,value,args); 
    if(compute_gradient) {
      pair<VentureValuePtr, vector<VentureValuePtr> > grad = scaffold->getLKernel(node)->gradientOfReverseWeight(trace, trace->getValue(node), args);
      db->addPartial(node, grad.first);
      // cout << "partial 2: " << endl;
      // cout << "grad " << toString(grad.second) << endl;
      db->addPartials(args->operandNodes, grad.second);
    }
  }
  db->registerValue(node,value);
  trace->clearValue(node);

  if(compute_gradient) {
    BOOST_FOREACH(Node* p, node->definiteParents) {
      if(scaffold->isResampling(p) || scaffold->isBrush(p)) {
        // cout << "psp type " << psp->toString() << endl;
        vector<VentureValuePtr> grads = psp->gradientOfSimulate(args, db->getValue(node), db->getPartial(node));
        vector<Node*> parents(args->operandNodes);
        vector<shared_ptr<Node> > parents_esr = trace->getESRParents(node);
        BOOST_FOREACH(shared_ptr<Node> node, parents_esr) 
          parents.push_back(node.get());
        // cout << "partial 3: " << endl;
        db->addPartials(parents, grads);
      }
    }
  }
  return weight;
}


double unevalRequests(ConcreteTrace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db, bool compute_gradient)
{
  //cout << "unevalRequests(" << node << ")" << endl;

  double weight = 0;

  const vector<ESR>& esrs = trace->getValue(node)->getESRs();
  const vector<shared_ptr<LSR> >& lsrs = trace->getValue(node)->getLSRs();
  
  Node * makerNode = trace->getOperatorSPMakerNode(node);
  shared_ptr<SP> sp = trace->getMadeSP(makerNode);
  shared_ptr<SPAux> spAux = trace->getMadeSPAux(makerNode);

  if (!lsrs.empty() && !db->hasLatentDB(makerNode)) { db->registerLatentDB(makerNode,sp->constructLatentDB()); }

  for (vector<shared_ptr<LSR> >::const_reverse_iterator lsrIter = lsrs.rbegin();
       lsrIter != lsrs.rend();
       ++lsrIter)
  {
    weight += sp->detachLatents(spAux,*lsrIter,db->getLatentDB(makerNode));
  }


  for (vector<ESR>::const_reverse_iterator esrIter = esrs.rbegin();
       esrIter != esrs.rend();
       ++esrIter)
  {
    RootOfFamily esrRoot = trace->popLastESRParent(node->outputNode);
    if (trace->getNumRequests(esrRoot) == 0)
    {
      trace->unregisterMadeSPFamily(trace->getOperatorSPMakerNode(node),esrIter->id);
      db->registerSPFamily(trace->getMadeSP(trace->getOperatorSPMakerNode(node)),esrIter->id,esrRoot);
      weight += unevalFamily(trace,esrRoot.get(),scaffold,db, compute_gradient);
    }
  }
  return weight;
}
