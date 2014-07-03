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
#include "math.h"

#include <time.h>
#include <boost/foreach.hpp>

/* Constructor */

ConcreteTrace::ConcreteTrace(): Trace(), rng(shared_ptr<RNGbox>(new RNGbox(gsl_rng_mt19937))) {}

void ConcreteTrace::initialize()
{
  rng->set_seed(time(NULL));

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
    builtInNodes.insert(shared_ptr<Node>(node));
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
    builtInNodes.insert(shared_ptr<Node>(node));
  }

  shared_ptr<VentureEnvironment> globalFrame (new VentureEnvironment(shared_ptr<VentureEnvironment>(),syms,nodes));
  // New frame so users can shadow globals
  globalEnvironment = shared_ptr<VentureEnvironment>(new VentureEnvironment(globalFrame));
}



/* Registering metadata */
void ConcreteTrace::registerAEKernel(Node * node) 
{ 
  assert(!arbitraryErgodicKernels.count(node));
  arbitraryErgodicKernels.insert(node);
}

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
  if (constrainedChoices.count(node) > 0)
  {
    throw "Cannot constrain the same random choice twice.";
  }
  
  constrainedChoices.insert(node);
  unregisterUnconstrainedChoice(node);
}

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) 
{
  assert(arbitraryErgodicKernels.count(node));
  arbitraryErgodicKernels.erase(node);
}


void ConcreteTrace::unregisterUnconstrainedChoice(Node * node) {
  unregisterUnconstrainedChoiceInScope(shared_ptr<VentureSymbol>(new VentureSymbol("default")),
                       shared_ptr<VentureNode>(new VentureNode(node)),
                       node);
  assert(unconstrainedChoices.count(node) == 1);
  unconstrainedChoices.erase(node);
}

void ConcreteTrace::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) 
{ 
  assert(scopes[scope].contains(block));
  assert(scopes[scope].get(block).count(node));
  scopes[scope].get(block).erase(node);
//  assert(scope->getSymbol() != "default" || scopes[scope].get(block).empty());
  if (scopes[scope].get(block).empty()) { scopes[scope].erase(block); }
  if (scopes[scope].size() == 0) { scopes.erase(scope); }
}

void ConcreteTrace::unregisterConstrainedChoice(Node * node) {
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
  incNumRequests(esrRoot);
  addChild(esrRoot.get(),outputNode);
  esrRoots[outputNode].push_back(esrRoot);
}

void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) 
{   
  addChild(lookupNode->sourceNode,lookupNode); 
}

void ConcreteTrace::incNumRequests(RootOfFamily root) { numRequests[root]++; }
void ConcreteTrace::incRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->incRegenCount(node); }

bool ConcreteTrace::hasLKernel(shared_ptr<Scaffold> scaffold, Node * node) { return scaffold->hasLKernel(node); }
void ConcreteTrace::registerLKernel(shared_ptr<Scaffold> scaffold,Node * node,shared_ptr<LKernel> lkernel) { scaffold->registerLKernel(node,lkernel); }
shared_ptr<LKernel> ConcreteTrace::getLKernel(shared_ptr<Scaffold> scaffold,Node * node) { return scaffold->getLKernel(node); }

void ConcreteTrace::addChild(Node * node, Node * child) 
{
  assert(node->children.count(child) == 0);
  node->children.insert(child);
}

/* Detach mutations */  
RootOfFamily ConcreteTrace::popLastESRParent(OutputNode * outputNode) 
{ 
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
  assert(numRequests.count(root));
  numRequests[root]--;
  if (numRequests[root] == 0) { numRequests.erase(root); }
}

void ConcreteTrace::decRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->decRegenCount(node); }
void ConcreteTrace::removeChild(Node * node, Node * child) 
{ 
  assert(node->children.count(child)); 
  node->children.erase(child);
}

/* Primitive getters */
gsl_rng * ConcreteTrace::getRNG() { return rng->get_rng(); }

VentureValuePtr ConcreteTrace::getValue(Node * node) 
{
  assert(values[node]); 
  return values[node]; 
}

shared_ptr<SP> ConcreteTrace::getMadeSP(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->sp;
}

shared_ptr<SPFamilies> ConcreteTrace::getMadeSPFamilies(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spFamilies;
}

shared_ptr<SPAux> ConcreteTrace::getMadeSPAux(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spAux;
}

shared_ptr<VentureSPRecord> ConcreteTrace::getMadeSPRecord(Node * makerNode) 
{
  assert(madeSPRecords.count(makerNode));
  return madeSPRecords[makerNode]; 
}
vector<RootOfFamily> ConcreteTrace::getESRParents(Node * node) 
{
  if (esrRoots.count(node)) { return esrRoots[node]; } 
  else { return vector<RootOfFamily>(); }
}

set<Node*> ConcreteTrace::getChildren(Node * node) { return node->children; }
int ConcreteTrace::getNumRequests(RootOfFamily root) 
{ 
  if (numRequests.count(root)) { return numRequests[root]; } 
  else { return 0; }
}
int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { return scaffold->getRegenCount(node); }

VentureValuePtr ConcreteTrace::getObservedValue(Node * node) { assert(observedValues.count(node)); return observedValues[node]; }

bool ConcreteTrace::isMakerNode(Node * node) { return madeSPRecords.count(node); }
bool ConcreteTrace::isConstrained(Node * node) { return constrainedChoices.count(node); }
bool ConcreteTrace::isObservation(Node * node) { return observedValues.count(node); }

/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) 
{ 
  assert(value); 
  values[node] = value; 
}

void ConcreteTrace::clearValue(Node * node) { values.erase(node); }

void ConcreteTrace::unobserveNode(Node * node)
{ 
  assert(observedValues.count(node));
  observedValues.erase(node);
}

void ConcreteTrace::observeNode(Node * node,VentureValuePtr value) 
{ 
  assert(!observedValues.count(node));
  observedValues[node] = value; 
}

void ConcreteTrace::setMadeSPRecord(Node * makerNode,shared_ptr<VentureSPRecord> spRecord)
{
  assert(!madeSPRecords.count(makerNode));
  madeSPRecords[makerNode] = spRecord;
}

void ConcreteTrace::destroyMadeSPRecord(Node * makerNode)
{
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
  esrRoots[node] = esrRootNodes;
}

void ConcreteTrace::setNumRequests(RootOfFamily node,int num) 
{ 
  //assert(false); 
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

BlockID ConcreteTrace::sampleBlock(ScopeID scope)
{
  if (!scopes.count(scope)) {
    throw "scope " + scope->toString() + " does not contain any blocks";
  }
  return scopes[scope].sampleKeyUniformly(getRNG());
}

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

vector<set<Node*> > ConcreteTrace::getOrderedSetsInScopeAndRange(ScopeID scope,BlockID minBlock,BlockID maxBlock)
{
  vector<set<Node*> > ordered;
  vector<BlockID> sortedBlocks = scopes[scope].getOrderedKeysInRange(minBlock,maxBlock);
  for (size_t i = 0; i < sortedBlocks.size(); ++ i)
    {
      set<Node*> nodesInBlock = getNodesInBlock(scope,sortedBlocks[i]);
      ordered.push_back(nodesInBlock);
    }
  return ordered;
}
    
vector<set<Node*> > ConcreteTrace::getOrderedSetsInScope(ScopeID scope) 
{ 
  vector<set<Node*> > ordered;
  vector<BlockID> sortedBlocks = scopes[scope].getOrderedKeys();
  for (size_t i = 0; i < sortedBlocks.size(); ++ i)
    {
      set<Node*> nodesInBlock = getNodesInBlock(scope,sortedBlocks[i]);
      ordered.push_back(nodesInBlock);
    }
  return ordered;
}

set<Node*> ConcreteTrace::getNodesInBlock(ScopeID scope, BlockID block) 
{ 
  if(!scopes[scope].contains(block))
  {
    throw "scope " + scope->toString() + " does not contain block " + block->toString();
  }
  
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
  if (psp->isRandom() && !isConstrained(outputNode)) { pnodes.insert(outputNode); }
  RequestNode * requestNode = outputNode->requestNode;
  shared_ptr<PSP> requestPSP = getMadeSP(getOperatorSPMakerNode(requestNode))->getPSP(requestNode);
  if (requestPSP->isRandom() && !isConstrained(requestNode)) { pnodes.insert(requestNode); }

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
    else if (i == 1 && dynamic_pointer_cast<ScopeExcludeOutputPSP>(psp))
    {
      ScopeID new_scope = getValue(outputNode->operandNodes[0]);
      if (!scope->equals(new_scope))
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

double ConcreteTrace::makeConsistent() 
{
  double weight = 0;
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
    pair<double,shared_ptr<DB> > p = detachAndExtract(this,scaffold->border[0],scaffold);
    double rhoWeight = p.first;
    assertTorus(scaffold);
    shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(appNode))->getPSP(appNode);
    scaffold->lkernels[appNode] = shared_ptr<DeterministicLKernel>(new DeterministicLKernel(iter->second,psp));
    double xiWeight = regenAndAttach(this,scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),shared_ptr<map<Node*,Gradient> >());
    if (std::isinf(xiWeight)) { throw "Unable to propagate constraint"; }
    observeNode(iter->first,iter->second);
    constrain(this,appNode,getObservedValue(iter->first));
    weight = weight + xiWeight - rhoWeight;
  }
  unpropagatedObservations.clear();
  return weight;
}

int ConcreteTrace::numUnconstrainedChoices() { return unconstrainedChoices.size(); }

int ConcreteTrace::getSeed() { assert(false); }
double ConcreteTrace::getGlobalLogScore() { assert(false); }


bool ConcreteTrace::hasAAAMadeSPAux(OutputNode * makerNode) { return aaaMadeSPAuxs.count(makerNode); }
void ConcreteTrace::discardAAAMadeSPAux(OutputNode * makerNode) { assert(aaaMadeSPAuxs.count(makerNode)); aaaMadeSPAuxs.erase(makerNode); }
void ConcreteTrace::registerAAAMadeSPAux(OutputNode * makerNode,shared_ptr<SPAux> spAux) { aaaMadeSPAuxs[makerNode] = spAux; }
shared_ptr<SPAux> ConcreteTrace::getAAAMadeSPAux(OutputNode * makerNode) { return aaaMadeSPAuxs[makerNode]; }


void ConcreteTrace::freezeDirectiveID(DirectiveID did)
{
  RootOfFamily root = families[did];
  OutputNode * outputNode = dynamic_cast<OutputNode*>(root.get());
  assert(outputNode);
  freezeOutputNode(outputNode);
}

void ConcreteTrace::freezeOutputNode(OutputNode * outputNode)
{
  VentureValuePtr curVal = getValue(outputNode);
  unevalFamily(this,outputNode,shared_ptr<Scaffold>(new Scaffold()),shared_ptr<DB>(new DB()));
  outputNode->isFrozen = true;
  outputNode->exp = curVal; // Get rid of the former expression; seems harmless and should save memory (and copying)
  setValue(outputNode, curVal);

  delete outputNode->requestNode;
  for (size_t i = 0; i < outputNode->operandNodes.size(); ++i) { delete outputNode->operandNodes[i]; }
  delete outputNode->operatorNode;

  outputNode->requestNode = NULL;
  outputNode->operandNodes.clear();
  outputNode->operatorNode = NULL;

}

template <typename K, typename V>
set<K> keySet(map<K, V> m)
{
  set<K> answer;
  pair<K, V> me;
  BOOST_FOREACH(me, m)
  {
    answer.insert(me.first);
  }
  return answer;

}
void ConcreteTrace::seekInconsistencies()
{
  typedef pair<RootOfFamily,int> countpair;
  BOOST_FOREACH(countpair p, numRequests)
  {
    if (p.second == 0)
    {
      cout << "Warning: found family with zero requests: " << p.first << " " << p.first->exp << endl;
    }
  }
  set<Node*> walkedNodes = allNodes();
  BOOST_FOREACH(Node* n, walkedNodes)
  {
    if (values.count(n) < 1)
    {
      cout << "Warning: found node with no value: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, unconstrainedChoices)
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling unconstrainedChoice entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, constrainedChoices)
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling constrainedChoice entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, arbitraryErgodicKernels)
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling arbitraryErgodicKernel entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, keySet(unpropagatedObservations))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling unpropagatedObservation entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, keySet(aaaMadeSPAuxs))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling aaaMadeSPAux entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, keySet(esrRoots))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling esrRoot entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, keySet(madeSPRecords))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling madeSPRecord entry: " << n << endl;
    } else {
      if (!dynamic_pointer_cast<VentureSPRef>(values[n]).get())
      {
        cout << "Warning: found node " << n << " with madeSPRecord entry but non-SPRef value " << values[n] << endl;
      } else {
        shared_ptr<VentureSPRef> spref(dynamic_pointer_cast<VentureSPRef>(values[n]));
        if (!(spref->makerNode == n))
        {
          cout << "Warning: found maker node " << n << " whose value is not a self-link" << endl;
        }
      }
    }
  }
  BOOST_FOREACH(Node* n, keySet(values))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling value entry: " << n << endl;
    }
  }
  BOOST_FOREACH(Node* n, keySet(observedValues))
  {
    if (walkedNodes.count(n) < 1)
    {
      cout << "Warning: found dangling observedValue entry: " << n << endl;
    }
  }
}

vector<Node*> familyParents(Node* node)
{
  vector<Node*> answer;
  if (dynamic_cast<ConstantNode*>(node)) { return vector<Node*>(); }
  if (dynamic_cast<LookupNode*>(node)) { return vector<Node*>(); }
  if (dynamic_cast<OutputNode*>(node))
  {
    answer.push_back(dynamic_cast<OutputNode*>(node)->requestNode);
    // The operator and operands will get picked up when traversing
    // the requester node
  }
  if (dynamic_cast<RequestNode*>(node))
  {
    RequestNode* n = dynamic_cast<RequestNode*>(node);
    answer.push_back(n->operatorNode);
    answer.insert(answer.end(), n->operandNodes.begin(), n->operandNodes.end());
  }
  return answer;
}

void addNodes(Node* root, set<Node*>& answer)
{
  if (root == NULL) { return; }
  assert(answer.count(root) == 0);
  answer.insert(root);
  BOOST_FOREACH(Node* p, familyParents(root))
  {
    addNodes(p, answer);
  }
}

set<Node*> ConcreteTrace::allNodes()
{
  set<Node*> answer;
  BOOST_FOREACH(shared_ptr<Node> node, builtInNodes)
  {
    assert(dynamic_cast<ConstantNode*>(node.get()));
    assert(answer.count(node.get()) == 0);
    answer.insert(node.get());
  }
  typedef pair<DirectiveID, RootOfFamily> family_map_entry;
  BOOST_FOREACH(family_map_entry fam, families)
  {
    Node* root(fam.second.get());
    addNodes(root, answer);
  }
  typedef pair<RootOfFamily, int> num_request_map_entry;
  BOOST_FOREACH(num_request_map_entry fam, numRequests)
  {
    Node* root(fam.first.get());
    addNodes(root, answer);
  }
  return answer;
}
