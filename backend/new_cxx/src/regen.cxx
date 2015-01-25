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
#include "srs.h"
#include "sps/scope.h"
#include <iostream>
#include <boost/foreach.hpp>


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
        OutputNode * outputNode = trace->getConstrainableNode(node);
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
    trace->setValue(node,psp->simulate(trace->getArgs(outputNode),trace->getRNG()));
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
  //cout << "attach(" << node << ")" << endl;

  double weight = regenParents(trace,node,scaffold,shouldRestore,db,gradients);
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);
  weight += psp->logDensity(groundValue,args);
  psp->incorporate(groundValue,args);

  if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  {
    ScopeID scope = trace->getValue(node->operandNodes[0]);
    BlockID block = trace->getValue(node->operandNodes[1]);
    Node * blockNode = node->operandNodes[2];
    trace->registerUnconstrainedChoiceInScope(scope,block,blockNode);
  }    

  return weight;
}


double regen(Trace * trace,
              Node * node,
              shared_ptr<Scaffold> scaffold,
              bool shouldRestore,
              shared_ptr<DB> db,
              shared_ptr<map<Node*,Gradient> > gradients)
{ 
  //cout << "regenOuter(" << node << ")" << endl;
  double weight = 0;
  if (scaffold->isResampling(node))
  {
    //cout << "regen(" << node << ") = " << trace->getRegenCount(scaffold,node) << endl;
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
  vector<Node*> definiteParents = node->getDefiniteParents();
  for (size_t i = 0; i < definiteParents.size(); ++i) { weight += regen(trace,definiteParents[i],scaffold,shouldRestore,db,gradients); }
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
  vector<RootOfFamily> esrRoots = trace->getESRParents(node);
  for (size_t i = 0; i < esrRoots.size(); ++i) { weight += regen(trace,esrRoots[i].get(),scaffold,shouldRestore,db,gradients); }
  return weight;
}

pair<double,Node*> evalFamily(Trace * trace,
                              VentureValuePtr exp,
                              shared_ptr<VentureEnvironment> env,
                              shared_ptr<Scaffold> scaffold,
                              bool shouldRestore,
                              shared_ptr<DB> db,
                              shared_ptr<map<Node*,Gradient> > gradients)
{
  if (isVariable(exp))
  {
    double weight = 0;
    shared_ptr<VentureSymbol> symbol = dynamic_pointer_cast<VentureSymbol>(exp);
    Node * sourceNode = env->lookupSymbol(symbol);
    weight = regen(trace,sourceNode,scaffold,shouldRestore,db,gradients);

    return make_pair(weight,trace->createLookupNode(sourceNode,exp));
  }
  else if (isSelfEvaluating(exp)) { return make_pair(0,trace->createConstantNode(exp)); }
  else if (isQuotation(exp)) { return make_pair(0,trace->createConstantNode(textOfQuotation(exp))); }
  else
  {
    assert(exp->hasArray());
    vector<VentureValuePtr> array = exp->getArray();
    pair<double,Node*> p = evalFamily(trace,array[0],env,scaffold,shouldRestore,db,gradients);
    double weight = p.first;
    Node * operatorNode = p.second;

    /* DEBUG */
    shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(trace->getValue(operatorNode));
    assert(spRef);
    /* END DEBUG */

    vector<Node*> operandNodes;
    for (size_t i = 1; i < array.size(); ++i)
    {
      pair<double,Node*>p = evalFamily(trace,array[i],env,scaffold,shouldRestore,db,gradients);
      weight += p.first;
      operandNodes.push_back(p.second);
    }

    pair<RequestNode*,OutputNode*> appNodes = trace->createApplicationNodes(operatorNode,operandNodes,env,exp);
    weight += apply(trace,appNodes.first,appNodes.second,scaffold,shouldRestore,db,gradients);
    return make_pair(weight,appNodes.second);
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
  const vector<ESR>& esrs = trace->getValue(requestNode)->getESRs();
  assert(trace->getESRParents(outputNode).size() == esrs.size());  
  /* END DEBUG */

  weight += regenESRParents(trace,outputNode,scaffold,shouldRestore,db,gradients);
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,db,gradients);

  return weight;
}



void processMadeSP(Trace * trace, Node * makerNode, bool isAAA, bool shouldRestore, shared_ptr<DB> db)
{
  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(trace->getValue(makerNode));
  assert(spRecord);
  shared_ptr<SP> sp = spRecord->sp;

  if (shouldRestore && db->hasMadeSPAux(makerNode)) { spRecord->spAux = db->getMadeSPAux(makerNode); }
  if (sp->hasAEKernel()) { trace->registerAEKernel(makerNode); }
  trace->setMadeSPRecord(makerNode,spRecord);
  if (isAAA) 
    { 
      OutputNode * outputNode = dynamic_cast<OutputNode*>(makerNode);
      assert(outputNode);
      trace->discardAAAMadeSPAux(outputNode); 
    }
  trace->setValue(makerNode,shared_ptr<VentureValue>(new VentureSPRef(makerNode)));
}

double applyPSP(Trace * trace,
              ApplicationNode * node,
              shared_ptr<Scaffold> scaffold,
              bool shouldRestore,
              shared_ptr<DB> db,
              shared_ptr<map<Node*,Gradient> > gradients)
{
  //cout << "applyPSP(" << node << ")" << endl;
  double weight = 0;
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);

  VentureValuePtr oldValue;
  VentureValuePtr newValue;

  if (db->hasValue(node)) { oldValue = db->getValue(node); }

  if (trace->hasLKernel(scaffold,node))
  {
    shared_ptr<LKernel> k = trace->getLKernel(scaffold,node);
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = k->simulate(trace,oldValue,args,trace->getRNG()); }

    weight += k->weight(trace,newValue,oldValue,args);
    /*
      These lines were causing problems, due to a mismatch between vector<double>
      and double in the gradientOfLogDensity. Puma doesn't actually have variational
      though, so I'm commenting these out for now.
      
    shared_ptr<VariationalLKernel> vk = dynamic_pointer_cast<VariationalLKernel>(k);
    if (vk) { 
      assert(gradients);
      gradients->insert(make_pair(node,vk->gradientOfLogDensity(newValue,args))); 
    }*/
  }
  else
  {
    if (shouldRestore) { newValue = oldValue; }
    else { newValue = psp->simulate(args,trace->getRNG()); } // TODO rng
  }

  if (dynamic_cast<RequestNode*>(node)) { assert(dynamic_pointer_cast<VentureRequest>(newValue)); }

  trace->setValue(node,newValue);

  psp->incorporate(newValue,args);

  if (dynamic_pointer_cast<VentureSPRecord>(newValue)) { processMadeSP(trace,node,scaffold->isAAA(node),shouldRestore,db); }
  if (psp->isRandom()) { trace->registerUnconstrainedChoice(node); }

  if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  {
    ScopeID scope = trace->getValue(node->operandNodes[0]);
    BlockID block = trace->getValue(node->operandNodes[1]);
    Node * blockNode = node->operandNodes[2];
    trace->registerUnconstrainedChoiceInScope(scope,block,blockNode);
  }
  return weight;
}


double evalRequests(Trace * trace,
              RequestNode * requestNode,
              shared_ptr<Scaffold> scaffold,
              bool shouldRestore,
              shared_ptr<DB> db,
              shared_ptr<map<Node*,Gradient> > gradients)
{
  //cout << "evalRequests(" << requestNode << "," << requestNode->outputNode << ")" << endl;

  double weight = 0;
  const vector<ESR>& esrs = trace->getValue(requestNode)->getESRs();
  const vector<shared_ptr<LSR> >& lsrs = trace->getValue(requestNode)->getLSRs();

  for (size_t i = 0; i < esrs.size(); ++i)
  {
    const ESR& esr = esrs[i];
    if (!trace->containsMadeSPFamily(trace->getOperatorSPMakerNode(requestNode),esr.id))
    {
      RootOfFamily esrRoot;
      shared_ptr<SP> sp = trace->getMadeSP(trace->getOperatorSPMakerNode(requestNode));
      if (shouldRestore && db->hasESRParent(sp, esr.id))
      {
        esrRoot = db->getESRParent(sp,esr.id);
        weight += restore(trace,esrRoot.get(),scaffold,db,gradients);
      }
      else
      {
        pair<double,Node*> p = evalFamily(trace,esr.exp,esr.env,scaffold,shouldRestore,db,gradients);
        weight += p.first;
        esrRoot = shared_ptr<Node>(p.second);
      }
      if (trace->containsMadeSPFamily(trace->getOperatorSPMakerNode(requestNode),esr.id))
      {
        // evalFamily already registered a family with this id for the
        // operator being applied here, which means a recursive call
        // to the operator issued a request for the same id.
        // Currently, the only way for that it happen is for a
        // recursive memmed function to call itself with the same
        // arguments.
        throw "Recursive mem argument loop detected.";
      }
      trace->registerMadeSPFamily(trace->getOperatorSPMakerNode(requestNode),esr.id,esrRoot);
    }
    RootOfFamily esrRoot = trace->getMadeSPFamilyRoot(trace->getOperatorSPMakerNode(requestNode),esr.id);
    trace->addESREdge(esrRoot,requestNode->outputNode);
    //cout << "numESRParents(" << requestNode->outputNode << ") = " << trace->getESRParents(requestNode->outputNode).size() << endl;
    assert(!trace->getESRParents(requestNode->outputNode).empty());
  }

  /* Next evaluate LSRs. */
  BOOST_FOREACH (shared_ptr<LSR> lsr, lsrs)
  {
    shared_ptr<LatentDB> latentDB;
    Node * makerNode = trace->getOperatorSPMakerNode(requestNode);
    shared_ptr<SP> sp = trace->getMadeSP(makerNode);
    shared_ptr<SPAux> spAux = trace->getMadeSPAux(makerNode);

    if (db->hasLatentDB(makerNode)) { latentDB = db->getLatentDB(makerNode); }

    weight += sp->simulateLatents(spAux,lsr,shouldRestore,latentDB,trace->getRNG());
  }

  return weight;
}



double restore(Trace * trace,
               Node * node,
               shared_ptr<Scaffold> scaffold,
               shared_ptr<DB> db,
               shared_ptr<map<Node*,Gradient> > gradients) 
{
  //cout << "restore(" << node << ")" << endl;

  double weight = 0;
  ConstantNode * constantNode = dynamic_cast<ConstantNode*>(node);
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);

  if (constantNode || (outputNode && outputNode->isFrozen))
  {
    trace->setValue(node, node->exp);
  }
  else if (lookupNode) 
  { 
    weight += regenParents(trace,lookupNode,scaffold,true,db,gradients);
    trace->reconnectLookup(lookupNode);
    trace->setValue(node,trace->getValue(lookupNode->sourceNode));
  }
  else
  {
    assert(outputNode);
    weight += restore(trace,outputNode->operatorNode,scaffold,db,gradients);
    for (size_t i = 0; i < outputNode->operandNodes.size(); ++i)
    {
      weight += restore(trace,outputNode->operandNodes[i],scaffold,db,gradients);
    }
    weight += apply(trace,outputNode->requestNode,outputNode,scaffold,true,db,gradients);
  }
  return weight;
}

