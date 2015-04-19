// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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

using std::cout;
using std::endl;

pair<double,shared_ptr<DB> > detachAndExtract(ConcreteTrace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold)
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
        weight += unconstrain(trace,trace->getConstrainableNode(node));
      }
      weight += extract(trace,node,scaffold,db);
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

double detach(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  //cout << "detach(" << node << ")" << endl;

  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);

  if (dynamic_pointer_cast<TagOutputPSP>(psp))
  {
    ScopeID scope = trace->getValue(node->operandNodes[0]);
    BlockID block = trace->getValue(node->operandNodes[1]);
    Node * blockNode = node->operandNodes[2];
    trace->unregisterUnconstrainedChoiceInScope(scope,block,blockNode);
  }

  psp->unincorporate(groundValue,args);
  double weight = psp->logDensity(groundValue,args);
  weight += extractParents(trace,node,scaffold,db);
  return weight;
}


double extractParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = extractESRParents(trace,node,scaffold,db);
  vector<Node*> definiteParents = node->getDefiniteParents();
  for (vector<Node*>::reverse_iterator defParentIter = definiteParents.rbegin();
       defParentIter != definiteParents.rend();
       ++defParentIter)
  {
    weight += extract(trace,*defParentIter,scaffold,db);
  }
  return weight;
}

double extractESRParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
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

double extract(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  //cout << "extractOuter(" << node << ")" << endl;
  double weight = 0;
  VentureValuePtr value = trace->getValue(node);

  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  if (spRef && spRef->makerNode != node && scaffold->isAAA(spRef->makerNode))
  {
    weight += extract(trace,spRef->makerNode,scaffold,db);
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
      if (lookupNode) { trace->clearValue(lookupNode); }
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

double unevalFamily(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  //cout << "unevalFamily(" << node << ")" << endl;
  double weight = 0;

  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode || (outputNode && outputNode->isFrozen) )
  {
    trace->clearValue(node);
  }
  else if (lookupNode)
  {
    trace->disconnectLookup(lookupNode);
    trace->clearValue(lookupNode);
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

double unapply(ConcreteTrace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = unapplyPSP(trace,node,scaffold,db);
  weight += extractESRParents(trace,node,scaffold,db);
  weight += unevalRequests(trace,node->requestNode,scaffold,db);
  weight += unapplyPSP(trace,node->requestNode,scaffold,db);
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

double unapplyPSP(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  //cout << "unapplyPSP(" << node << ")" << endl;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);


  // TODO Tag
  if (dynamic_pointer_cast<TagOutputPSP>(psp))
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
  if (trace->hasLKernel(scaffold,node)) { weight += trace->getLKernel(scaffold,node)->reverseWeight(trace,value,args); }
  db->registerValue(node,value);

  trace->clearValue(node);

  return weight;
}


double unevalRequests(ConcreteTrace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
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
      weight += unevalFamily(trace,esrRoot.get(),scaffold,db);
    }
  }
  return weight;
}
