#include "concrete_trace.h"
#include "values.h"
#include "detach.h"
#include "env.h"
#include "builtin.h"
#include "lkernel.h"
#include "regen.h"
#include "sp.h"
#include "db.h"

#include <cmath>
#include <cfloat>
#include <cassert>

#include <iostream>
using std::cout;
using std::endl;

/* Constructor */

ConcreteTrace::ConcreteTrace(): Trace()
{
  vector<shared_ptr<VentureSymbol> > syms;
  vector<Node*> nodes;

  map<string,VentureValuePtr> builtInValues = initBuiltInValues();
  map<string,shared_ptr<VentureSP> > builtInSPs = initBuiltInSPs();

  for (map<string,VentureValuePtr>::iterator iter = builtInValues.begin();
       iter != builtInValues.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym(new VentureSymbol(iter->first));
    ConstantNode * node = createConstantNode(static_pointer_cast<VentureValue>(iter->second));
    syms.push_back(sym);
    nodes.push_back(node);
  }

  for (map<string,shared_ptr<VentureSP> >::iterator iter = builtInSPs.begin();
       iter != builtInSPs.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym(new VentureSymbol(iter->first));
    ConstantNode * node = createConstantNode(static_pointer_cast<VentureValue>(iter->second));
    processMadeSP(this,node,false,shared_ptr<DB>(new DB()));
    assert(dynamic_pointer_cast<VentureSPRef>(getValue(node)));
    syms.push_back(sym);
    nodes.push_back(node);
  }

  globalEnvironment = shared_ptr<VentureEnvironment>(new VentureEnvironment(shared_ptr<VentureEnvironment>(),syms,nodes));
}



/* Registering metadata */
void ConcreteTrace::registerAEKernel(Node * node) { assert(false); }

void ConcreteTrace::registerUnconstrainedChoice(Node * node) {
  assert(unconstrainedChoices.count(node) == 0);
  unconstrainedChoices.insert(node);
  registerUnconstrainedChoiceInScope(shared_ptr<VentureSymbol>(new VentureSymbol("default")),
				     shared_ptr<VentureNode>(new VentureNode(node)),
				     node);
}

void ConcreteTrace::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  assert(block);
  if (!scopes.count(scope)) { scopes[scope] = SamplableMap<BlockID,set<Node*> >(); }
  if (!scopes[scope].contains(block)) { scopes[scope].set(block,set<Node*>()); }
  assert(!scopes[scope].get(block).count(node));
  scopes[scope].get(block).insert(node);
  assert(scope->getSymbol() != "default" || scopes[scope].get(block).size() == 1);
}

void ConcreteTrace::registerConstrainedChoice(Node * node) {
  assert(constrainedChoices.count(node) == 0);
  constrainedChoices.insert(node);
}

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) { assert(false); }

void ConcreteTrace::unregisterUnconstrainedChoice(Node * node) {
  unregisterUnconstrainedChoiceInScope(shared_ptr<VentureSymbol>(new VentureSymbol("default")),
				       shared_ptr<VentureNode>(new VentureNode(node)),
				       node);
  assert(unconstrainedChoices.count(node) == 1);
  unconstrainedChoices.erase(node);
}

void ConcreteTrace::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  assert(scopes[scope].get(block).count(node));
  scopes[scope].get(block).erase(node);
  assert(scope->getSymbol() != "default" || scopes[scope].get(block).empty());
  if (scopes[scope].get(block).empty()) { scopes[scope].erase(block); }
  if (scopes[scope].size() == 0) { scopes.erase(scope); }
}

void ConcreteTrace::unregisterConstrainedChoice(Node * node) {
  assert(constrainedChoices.count(node) == 1);
  constrainedChoices.erase(node);
}

/* Regen mutations */
void ConcreteTrace::addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) 
{
  incNumRequests(esrRoot);
  addChild(esrRoot.get(),outputNode);
  esrRoots[outputNode].push_back(esrRoot);
}

void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) { addChild(lookupNode->sourceNode,lookupNode); }
void ConcreteTrace::incNumRequests(RootOfFamily root) { numRequests[root]++; }
void ConcreteTrace::incRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->incRegenCount(node); }
void ConcreteTrace::addChild(Node * node, Node * child) 
{
  assert(children[node].count(child) == 0);
  children[node].insert(child);
}

/* Detach mutations */  
RootOfFamily ConcreteTrace::popLastESRParent(OutputNode * outputNode) 
{ 
  vector<RootOfFamily> esrRoots = getESRParents(outputNode);
  assert(!esrRoots.empty());
  RootOfFamily esrRoot = esrRoots.back();
  esrRoots.pop_back();
  removeChild(esrRoot.get(),outputNode);
  decNumRequests(esrRoot);
  return esrRoot;
}

void ConcreteTrace::disconnectLookup(LookupNode * lookupNode) { removeChild(lookupNode->sourceNode,lookupNode); }
void ConcreteTrace::decNumRequests(RootOfFamily root) 
{ 
  assert(numRequests.count(root));
  numRequests[root]--;
}

void ConcreteTrace::decRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->decRegenCount(node); }
void ConcreteTrace::removeChild(Node * node, Node * child) { assert(children.count(node)); children[node].erase(child); }

/* Primitive getters */
VentureValuePtr ConcreteTrace::getValue(Node * node) { return values[node]; }
SPRecord ConcreteTrace::getMadeSPRecord(Node * makerNode) 
{
  assert(madeSPRecords.count(makerNode));
  return madeSPRecords[makerNode]; 
}
vector<RootOfFamily> ConcreteTrace::getESRParents(Node * node) { return esrRoots[node]; }
set<Node*> ConcreteTrace::getChildren(Node * node) { return children[node]; }
int ConcreteTrace::getNumRequests(RootOfFamily root) { return numRequests[root]; }
int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { return scaffold->getRegenCount(node); }

VentureValuePtr ConcreteTrace::getObservedValue(Node * node) { return observedValues[node]; }

bool ConcreteTrace::isMakerNode(Node * node) { return madeSPRecords.count(node); }
bool ConcreteTrace::isConstrained(Node * node) { return constrainedChoices.count(node); }
bool ConcreteTrace::isObservation(Node * node) { return observedValues.count(node); }


/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) { values[node] = value; }
void ConcreteTrace::clearValue(Node * node) { values.erase(node); }

void ConcreteTrace::observeNode(Node * node,VentureValuePtr value) 
{ 
  assert(!observedValues.count(node));
  observedValues[node] = value; 
}

void ConcreteTrace::initMadeSPRecord(Node * makerNode,shared_ptr<VentureSP> sp,shared_ptr<SPAux> spAux)
{
  assert(!madeSPRecords.count(makerNode));
  SPRecord spRecord;
  spRecord.sp = sp;
  spRecord.spAux = spAux;
  spRecord.spFamilies = shared_ptr<SPFamilies>(new SPFamilies());
  madeSPRecords[makerNode] = spRecord;
}

void ConcreteTrace::destroyMadeSPRecord(Node * makerNode)
{
  assert(madeSPRecords.count(makerNode));
  madeSPRecords.erase(makerNode);
}


void ConcreteTrace::setMadeSP(Node * makerNode,shared_ptr<VentureSP> sp) 
{
  getMadeSPRecord(makerNode).sp = sp;
}
void ConcreteTrace::setMadeSPAux(Node * makerNode,shared_ptr<SPAux> spAux) 
{ 
  getMadeSPRecord(makerNode).spAux = spAux;
}

void ConcreteTrace::setChildren(Node * node,set<Node*> childNodes) 
{ 
  assert(false); 
  children[node] = childNodes;
}
void ConcreteTrace::setESRParents(Node * node,const vector<RootOfFamily> & esrRootNodes) 
{
  assert(false);
  esrRoots[node] = esrRootNodes;
}

void ConcreteTrace::setNumRequests(Node * node,int num) 
{ 
  assert(false); 
//  numRequests[node] = num;
}

/* SPFamily operations */
void ConcreteTrace::registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot)
{
  getMadeSPFamilies(makerNode)->registerFamily(id,esrRoot);
}

void ConcreteTrace::unregisterMadeSPFamily(Node * makerNode,FamilyID id)
{
  getMadeSPFamilies(makerNode)->unregisterFamily(id);
}

bool ConcreteTrace::containsMadeSPFamily(Node * makerNode, FamilyID id) 
{ 
  return getMadeSPFamilies(makerNode)->containsFamily(id);
}

RootOfFamily ConcreteTrace::getMadeSPFamilyRoot(Node * makerNode, FamilyID id)
{
  return getMadeSPFamilies(makerNode)->getRootOfFamily(id);
}


/* New in ConcreteTrace */

BlockID ConcreteTrace::sampleBlock(ScopeID scope) { return scopes[scope].sampleKeyUniformly(rng); }
double ConcreteTrace::logDensityOfBlock(ScopeID scope) { return -1 * log(numBlocksInScope(scope)); }
//vector<BlockID> ConcreteTrace::blocksInScope(ScopeID scope) { assert(false); }
int ConcreteTrace::numBlocksInScope(ScopeID scope) 
{ 
  if (scopes.count(scope)) { return scopes[scope].size(); }
  else { return 0; }
}

set<Node*> ConcreteTrace::getAllNodesInScope(ScopeID scope) 
{ 
  set<Node*> all;
  // TODO have SamplableMap provide an iterator
  for (map<VentureValuePtr,int>::iterator iter = scopes[scope].d.begin();
       iter != scopes[scope].d.end();
       ++iter)
  {
    set<Node*> nodesInBlock = getNodesInBlock(scope,iter->first);
    all.insert(nodesInBlock.begin(),nodesInBlock.end());
  }
  return all;
}

    
vector<set<Node*> > ConcreteTrace::getOrderedSetsInScope(ScopeID scope) { assert(false); }

set<Node*> ConcreteTrace::getNodesInBlock(ScopeID scope, BlockID block) 
{ 
  set<Node * > nodes = scopes[scope].get(block);
  if (dynamic_pointer_cast<VentureSymbol>(scope) && scope->getSymbol() == "default") { return nodes; }
  set<Node *> pnodes;
  for (set<Node*>::iterator iter = nodes.begin();
       iter != nodes.end();
       ++iter)
  {
    addUnconstrainedChoicesInBlock(scope,block,pnodes,*iter);
  }
  return pnodes;
}

void ConcreteTrace::addUnconstrainedChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node) 
{ 
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
  if (!outputNode) { return; }
  shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
  if (psp->isRandom()) { pnodes.insert(outputNode); }
  RequestNode * requestNode = outputNode->requestNode;
  shared_ptr<PSP> requestPSP = getMadeSP(getOperatorSPMakerNode(requestNode))->getPSP(requestNode);
  if (requestPSP->isRandom()) { pnodes.insert(requestNode); }

  const vector<ESR>& esrs = getValue(requestNode)->getESRs();
  Node * makerNode = getOperatorSPMakerNode(requestNode);
  for (size_t i = 0; i < esrs.size(); ++i) { addUnconstrainedChoicesInBlock(scope,block,pnodes,getMadeSPFamilyRoot(makerNode,esrs[i].id).get()); }

  addUnconstrainedChoicesInBlock(scope,block,pnodes,outputNode->operatorNode);
  for (size_t i = 0; i < outputNode->operandNodes.size(); ++i)
  {
    Node * operandNode = outputNode->operandNodes[i];
    // TODO once we implement ScopeIncludeOutputPSP
    // if (i == 2 && dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
    // {
    //   ScopeID new_scope = getValue(outputNode->operandNodes[0]);
    //   BlockID new_block = getValue(outputNode->operandNodes[1]);
    //   if (!scope->equals(new_scope) || block->equals(new_block))
    //   {
    // 	addUnconstrainedChoicesInBlock(scope,block,pnodes,operandNode);
    //   }
    // }
    // else
    // {
      addUnconstrainedChoicesInBlock(scope,block,pnodes,operandNode);
//    }
  }
}

bool ConcreteTrace::scopeHasEntropy(ScopeID scope) 
{ 
  return scopes.count(scope) && numBlocksInScope(scope) > 0; 
}

void ConcreteTrace::makeConsistent() 
{
  for (map<Node*,VentureValuePtr>::iterator iter = unpropagatedObservations.begin();
       iter != unpropagatedObservations.end();
       ++iter)
  {
    OutputNode * appNode = getOutermostNonRefAppNode(iter->first);
    vector<set<Node*> > setsOfPNodes;
    set<Node*> pnodes;
    pnodes.insert(appNode);
    setsOfPNodes.push_back(pnodes);
    shared_ptr<Scaffold> scaffold = constructScaffold(this,setsOfPNodes);
    detachAndExtract(this,scaffold->border[0],scaffold);
//    assertTorus(scaffold); // TODO
    shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(appNode))->getPSP(appNode);
    scaffold->lkernels[appNode] = shared_ptr<DeterministicLKernel>(new DeterministicLKernel(iter->second,psp));
    double xiWeight = regenAndAttach(this,scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),shared_ptr<map<Node*,Gradient> >());
    if (isinf(xiWeight)) { assert(false); throw "Unable to propagate constraint"; }
    observeNode(iter->first,iter->second);
    constrain(this,appNode,getObservedValue(iter->first));
  }
  unpropagatedObservations.clear();
}

int ConcreteTrace::numUnconstrainedChoices() { return unconstrainedChoices.size(); }

int ConcreteTrace::getSeed() { assert(false); }
double ConcreteTrace::getGlobalLogScore() { assert(false); }

//void ConcreteTrace::addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies) { assert(false); }
//void ConcreteTrace::addNewChildren(Node * node,PSet newChildren) { assert(false); }
