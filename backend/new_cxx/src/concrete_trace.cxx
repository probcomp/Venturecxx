#include "concrete_trace.h"
#include "values.h"
#include "consistency.h"
#include "detach.h"
#include "env.h"
#include "builtin.h"
#include "lkernel.h"
#include "regen.h"
#include "sp.h"
#include "db.h"
#include "sps/scope.h"
#include <cmath>
#include <cfloat>
#include <cassert>

#include <iostream>

typedef boost::shared_lock<boost::shared_mutex> ReaderLock;
typedef boost::upgrade_lock<boost::shared_mutex> UpgradeLock;
typedef boost::upgrade_to_unique_lock<boost::shared_mutex> UpgradeToUniqueLock;
typedef boost::unique_lock<boost::mutex> UniqueLock;

using std::cout;
using std::endl;

/* Constructor */

ConcreteTrace::ConcreteTrace(): Trace(), rng(gsl_rng_alloc(gsl_rng_mt19937))
{
  gsl_rng_set (rng,time(NULL));

  vector<shared_ptr<VentureSymbol> > syms;
  vector<Node*> nodes;

  map<string,VentureValuePtr> builtInValues = initBuiltInValues();
  map<string,SP *> builtInSPs = initBuiltInSPs();

  for (map<string,VentureValuePtr>::iterator iter = builtInValues.begin();
       iter != builtInValues.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym(new VentureSymbol(iter->first));
    ConstantNode * node = createConstantNode(iter->second);
    syms.push_back(sym);
    nodes.push_back(node);
  }

  for (map<string,SP *>::iterator iter = builtInSPs.begin();
       iter != builtInSPs.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym(new VentureSymbol(iter->first));
    ConstantNode * node = createConstantNode(VentureValuePtr(new VentureSPRecord(iter->second)));
    processMadeSP(this,node,false,false,shared_ptr<DB>(new DB()));
    assert(dynamic_pointer_cast<VentureSPRef>(getValue(node)));
    syms.push_back(sym);
    nodes.push_back(node);
  }

  globalEnvironment = shared_ptr<VentureEnvironment>(new VentureEnvironment(shared_ptr<VentureEnvironment>(),syms,nodes));
}



/* Registering metadata */
void ConcreteTrace::registerAEKernel(Node * node) 
{
  UniqueLock l(_mutex_arbitraryErgodicKernels);
  assert(!arbitraryErgodicKernels.count(node));
  arbitraryErgodicKernels.insert(node);
}

void ConcreteTrace::registerUnconstrainedChoice(Node * node) {
  UniqueLock l(_mutex_unconstrainedChoices);
  assert(unconstrainedChoices.count(node) == 0);
  unconstrainedChoices.insert(node);
  registerUnconstrainedChoiceInScope(shared_ptr<VentureSymbol>(new VentureSymbol("default")),
				     shared_ptr<VentureNode>(new VentureNode(node)),
				     node);
}

void ConcreteTrace::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  UniqueLock l(_mutex_scopes);
  assert(block);
  if (!scopes.count(scope)) { scopes[scope]/* = SamplableMap<BlockID,set<Node*> >()*/; }
  if (!scopes[scope].contains(block)) { scopes[scope].set(block,set<Node*>()); }
  assert(scopes[scope].contains(block));
  assert(!scopes[scope].get(block).count(node));
  scopes[scope].get(block).insert(node);
  assert(scopes[scope].size() > 0);
  assert(scopes[scope].get(block).size() > 0);
//  assert(scope->getSymbol() != "default" || scopes[scope].get(block).size() == 1);
}

void ConcreteTrace::registerConstrainedChoice(Node * node) {
  UpgradeLock l(_mutex_constrainedChoices);
  UpgradeToUniqueLock ll(l);
  assert(constrainedChoices.count(node) == 0);
  constrainedChoices.insert(node);
  unregisterUnconstrainedChoice(node);
}

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) 
{
  UniqueLock l(_mutex_arbitraryErgodicKernels);
  assert(arbitraryErgodicKernels.count(node));
  arbitraryErgodicKernels.erase(node);
}


void ConcreteTrace::unregisterUnconstrainedChoice(Node * node) {
  UniqueLock l(_mutex_unconstrainedChoices);
  unregisterUnconstrainedChoiceInScope(shared_ptr<VentureSymbol>(new VentureSymbol("default")),
				       shared_ptr<VentureNode>(new VentureNode(node)),
				       node);
  assert(unconstrainedChoices.count(node) == 1);
  unconstrainedChoices.erase(node);
}

void ConcreteTrace::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  UniqueLock l(_mutex_scopes);
  assert(scopes[scope].contains(block));
  assert(scopes[scope].get(block).count(node));
  scopes[scope].get(block).erase(node);
//  assert(scope->getSymbol() != "default" || scopes[scope].get(block).empty());
  if (scopes[scope].get(block).empty()) { scopes[scope].erase(block); }
  if (scopes[scope].size() == 0) { scopes.erase(scope); }
}

void ConcreteTrace::unregisterConstrainedChoice(Node * node) {
  UpgradeLock l(_mutex_constrainedChoices);
  UpgradeToUniqueLock ll(l);

  assert(constrainedChoices.count(node) == 1);
  constrainedChoices.erase(node);
  ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
  assert(appNode);
  shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(appNode))->getPSP(appNode);
  if (psp->isRandom()) { registerUnconstrainedChoice(appNode); }
}

/* Regen mutations */
void ConcreteTrace::addESREdge(RootOfFamily esrRoot,OutputNode * outputNode) 
{
  UpgradeLock l(_mutex_esrRoots);
  UpgradeToUniqueLock ll(l);
  incNumRequests(esrRoot);
  addChild(esrRoot.get(),outputNode);
  esrRoots[outputNode].push_back(esrRoot);
}

void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) 
{   
  addChild(lookupNode->sourceNode,lookupNode); 
}

void ConcreteTrace::incNumRequests(RootOfFamily root) 
{ 
  UpgradeLock l(_mutex_numRequests);
  UpgradeToUniqueLock ll(l);
  numRequests[root]++; 
}

void ConcreteTrace::incRegenCount(shared_ptr<Scaffold> scaffold, Node * node)
{
  UpgradeLock l(_mutex_regenCounts);
  UpgradeToUniqueLock ll(l);
  scaffold->incRegenCount(node);
}

void ConcreteTrace::addChild(Node * node, Node * child) 
{
  UpgradeLock l(_mutex_children);
  UpgradeToUniqueLock ll(l);
  assert(node->children.count(child) == 0);
  node->children.insert(child);
}

/* Detach mutations */  
RootOfFamily ConcreteTrace::popLastESRParent(OutputNode * outputNode) 
{ 
  UpgradeLock l(_mutex_esrRoots);
  UpgradeToUniqueLock ll(l);

  vector<RootOfFamily> & esrParents = esrRoots[outputNode];
  assert(!esrParents.empty());
  RootOfFamily esrRoot = esrParents.back();
  esrParents.pop_back();
  removeChild(esrRoot.get(),outputNode);
  decNumRequests(esrRoot);
  return esrRoot;
}

void ConcreteTrace::disconnectLookup(LookupNode * lookupNode) 
{
  removeChild(lookupNode->sourceNode,lookupNode); 
}
void ConcreteTrace::decNumRequests(RootOfFamily root) 
{ 
  UpgradeLock l(_mutex_numRequests);
  UpgradeToUniqueLock ll(l);

  assert(numRequests.count(root));
  numRequests[root]--;
}

void ConcreteTrace::decRegenCount(shared_ptr<Scaffold> scaffold, Node * node) 
{
  UpgradeLock l(_mutex_regenCounts);
  UpgradeToUniqueLock ll(l);
  scaffold->decRegenCount(node); 
}

void ConcreteTrace::removeChild(Node * node, Node * child) 
{ 
  UpgradeLock l(_mutex_children);
  UpgradeToUniqueLock ll(l);
  assert(node->children.count(child)); 
  node->children.erase(child);
}

/* Primitive getters */
gsl_rng * ConcreteTrace::getRNG() { return rng; }
VentureValuePtr ConcreteTrace::getValue(Node * node) 
{ 
  ReaderLock l(_mutex_values);
  assert(values[node]); 
  return values[node]; 
}
shared_ptr<SP> ConcreteTrace::getMadeSP(Node * makerNode)
{
  ReaderLock l(_mutex_madeSPRecords);
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->sp;
}

shared_ptr<SPFamilies> ConcreteTrace::getMadeSPFamilies(Node * makerNode)
{
  ReaderLock l(_mutex_madeSPRecords);
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spFamilies;
}

shared_ptr<SPAux> ConcreteTrace::getMadeSPAux(Node * makerNode)
{
  ReaderLock l(_mutex_madeSPRecords);
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spAux;
}

shared_ptr<VentureSPRecord> ConcreteTrace::getMadeSPRecord(Node * makerNode) 
{
  ReaderLock l(_mutex_madeSPRecords);
  assert(madeSPRecords.count(makerNode));
  return madeSPRecords[makerNode]; 
}
vector<RootOfFamily> ConcreteTrace::getESRParents(Node * node) 
{ 
  ReaderLock l(_mutex_esrRoots);
  return esrRoots[node]; 
}
set<Node*> ConcreteTrace::getChildren(Node * node) 
{ 
  ReaderLock l(_mutex_children);
  return node->children; 
}

int ConcreteTrace::getNumRequests(RootOfFamily root) 
{ 
  ReaderLock l(_mutex_numRequests);
  return numRequests[root]; 
}
int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) 
{ 
  ReaderLock l(_mutex_regenCounts);
  return scaffold->getRegenCount(node);
}

VentureValuePtr ConcreteTrace::getObservedValue(Node * node) 
{
  ReaderLock l(_mutex_observedValues);
  return observedValues[node]; 
}

bool ConcreteTrace::isMakerNode(Node * node) 
{ 
  ReaderLock l(_mutex_madeSPRecords);
  return madeSPRecords.count(node); 
}
bool ConcreteTrace::isConstrained(Node * node) 
{ 
  ReaderLock l(_mutex_constrainedChoices);
  return constrainedChoices.count(node); 
}
bool ConcreteTrace::isObservation(Node * node) 
{ 
  ReaderLock l(_mutex_observedValues);
  return observedValues.count(node); 
}

/* Derived Getters */
shared_ptr<PSP> ConcreteTrace::getPSP(ApplicationNode * node)
{
  return getMadeSP(getOperatorSPMakerNode(node))->getPSP(node);
}

/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) 
{ 
  UpgradeLock l(_mutex_values);
  UpgradeToUniqueLock ll(l);
  assert(value); 
  values[node] = value; 
}

void ConcreteTrace::clearValue(Node * node) 
{
  UpgradeLock l(_mutex_values);
  UpgradeToUniqueLock ll(l);
  values.erase(node);
}

void ConcreteTrace::unobserveNode(Node * node)
{ 
  UpgradeLock l(_mutex_observedValues);
  UpgradeToUniqueLock ll(l);

  assert(observedValues.count(node));
  observedValues.erase(node);
}

void ConcreteTrace::observeNode(Node * node,VentureValuePtr value) 
{ 
  UpgradeLock l(_mutex_observedValues);
  UpgradeToUniqueLock ll(l);

  assert(!observedValues.count(node));
  observedValues[node] = value; 
}

void ConcreteTrace::setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord)
{
  UpgradeLock l(_mutex_madeSPRecords);
  UpgradeToUniqueLock ll(l);

  assert(!madeSPRecords.count(makerNode));
  madeSPRecords[makerNode] = spRecord;
}

void ConcreteTrace::destroyMadeSPRecord(Node * makerNode)
{
  UpgradeLock l(_mutex_madeSPRecords);
  UpgradeToUniqueLock ll(l);

  assert(madeSPRecords.count(makerNode));
  madeSPRecords.erase(makerNode);
}


void ConcreteTrace::setMadeSP(Node * makerNode,shared_ptr<SP> sp) 
{
  getMadeSPRecord(makerNode)->sp = sp;
}
void ConcreteTrace::setMadeSPAux(Node * makerNode,shared_ptr<SPAux> spAux) 
{ 
  getMadeSPRecord(makerNode)->spAux = spAux;
}

void ConcreteTrace::setChildren(Node * node,set<Node*> childNodes) 
{ 
  assert(false); 
  //  children[node] = childNodes;
}
void ConcreteTrace::setESRParents(Node * node,const vector<RootOfFamily> & esrRootNodes) 
{
  UpgradeLock l(_mutex_esrRoots);
  UpgradeToUniqueLock ll(l);
  esrRoots[node] = esrRootNodes;
}

void ConcreteTrace::setNumRequests(RootOfFamily node,int num) 
{ 
  UpgradeLock l(_mutex_numRequests);
  UpgradeToUniqueLock ll(l);
  numRequests[node] = num;
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

BlockID ConcreteTrace::sampleBlock(ScopeID scope) { assert(scopes.count(scope)); return scopes[scope].sampleKeyUniformly(rng); }

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
  for (vector<pair<BlockID,set<Node*> > >::iterator iter = scopes[scope].a.begin();
       iter != scopes[scope].a.end();
       ++iter)
  {
    set<Node*> nodesInBlock = getNodesInBlock(scope,iter->first);
    all.insert(nodesInBlock.begin(),nodesInBlock.end());
  }
  return all;
}

    
vector<set<Node*> > ConcreteTrace::getOrderedSetsInScope(ScopeID scope) 
{ 
  vector<set<Node*> > ordered;
  
  for (vector<pair<BlockID,set<Node*> > >::iterator iter = scopes[scope].a.begin();
       iter != scopes[scope].a.end();
       ++iter)
    {
      set<Node*> nodesInBlock = getNodesInBlock(scope,iter->first);
      ordered.push_back(nodesInBlock);
    }
  return ordered;
}

set<Node*> ConcreteTrace::getNodesInBlock(ScopeID scope, BlockID block) 
{ 
  assert(scopes[scope].contains(block));
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
    if (i == 2 && dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
    {
      ScopeID new_scope = getValue(outputNode->operandNodes[0]);
      BlockID new_block = getValue(outputNode->operandNodes[1]);
      if (!scope->equals(new_scope) || block->equals(new_block))
      {
    	addUnconstrainedChoicesInBlock(scope,block,pnodes,operandNode);
      }
    }
    else
    {
      addUnconstrainedChoicesInBlock(scope,block,pnodes,operandNode);
    }
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
    shared_ptr<Scaffold> scaffold = constructScaffold(this,setsOfPNodes,false);
    detachAndExtract(this,scaffold->border[0],scaffold);
    assertTorus(scaffold);
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


bool ConcreteTrace::hasAAAMadeSPAux(OutputNode * makerNode) { return aaaMadeSPAuxs.count(makerNode); }
void ConcreteTrace::discardAAAMadeSPAux(OutputNode * makerNode) { assert(aaaMadeSPAuxs.count(makerNode)); aaaMadeSPAuxs.erase(makerNode); }
void ConcreteTrace::registerAAAMadeSPAux(OutputNode * makerNode,shared_ptr<SPAux> spAux) { aaaMadeSPAuxs[makerNode] = spAux; }
shared_ptr<SPAux> ConcreteTrace::getAAAMadeSPAux(OutputNode * makerNode) { return aaaMadeSPAuxs[makerNode]; }
