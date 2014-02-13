#include "concrete_trace.h"
#include "values.h"
#include "env.h"
#include "builtin.h"
#include "regen.h"
#include "sp.h"
#include "db.h"

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
}

void ConcreteTrace::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) { assert(false); }

void ConcreteTrace::registerConstrainedChoice(Node * node) {
  assert(constrainedChoices.count(node) == 0);
  constrainedChoices.insert(node);
}

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) { assert(false); }

void ConcreteTrace::unregisterUnconstrainedChoice(Node * node) {
  assert(unconstrainedChoices.count(node) == 1);
  unconstrainedChoices.erase(node);
}

void ConcreteTrace::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) { assert(false); }

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

void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) { assert(false); }
void ConcreteTrace::incNumRequests(RootOfFamily root) { assert(false); }
void ConcreteTrace::incRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->incRegenCount(node); }
void ConcreteTrace::addChild(Node * node, Node * child) 
{
  assert(children[node].count(child) == 0);
  children[node].insert(child);
}

/* Detach mutations */  
RootOfFamily ConcreteTrace::popLastESRParent(OutputNode * outputNode) { assert(false); }
void ConcreteTrace::disconnectLookup(LookupNode * lookupNode) { assert(false); }
void ConcreteTrace::decNumRequests(RootOfFamily root) { assert(false); }
void ConcreteTrace::decRegenCount(shared_ptr<Scaffold> scaffold, Node * node) { scaffold->decRegenCount(node); }
void ConcreteTrace::removeChild(Node * node, Node * child) { assert(false); }

/* Primitive getters */
VentureValuePtr ConcreteTrace::getValue(Node * node) { return values[node]; }
SPRecord ConcreteTrace::getMadeSPRecord(Node * makerNode) { return madeSPRecords[makerNode]; }
vector<RootOfFamily> ConcreteTrace::getESRParents(Node * node) { return esrRoots[node]; }
set<Node*> ConcreteTrace::getChildren(Node * node) { return children[node]; }
int ConcreteTrace::getNumRequests(RootOfFamily root) { return numRequests[root]; }
int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { assert(false); }

VentureValuePtr ConcreteTrace::getObservedValue(Node * node) { return observedValues[node]; }
bool ConcreteTrace::isConstrained(Node * node) { return constrainedChoices.count(node); }
bool ConcreteTrace::isObservation(Node * node) { return observedValues.count(node); }


/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) { values[node] = value; }
void ConcreteTrace::clearValue(Node * node) { values.erase(node); }


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





void ConcreteTrace::setMadeSP(Node * node,shared_ptr<VentureSP> sp) { assert(false); }
void ConcreteTrace::setMadeSPAux(Node * node,shared_ptr<SPAux> spaux) { assert(false); }

void ConcreteTrace::setChildren(Node * node,set<Node*> children) { assert(false); }
void ConcreteTrace::setESRParents(Node * node,const vector<RootOfFamily> & esrRoots) { assert(false); }

void ConcreteTrace::setNumRequests(Node * node,int num) { assert(false); }

/* SPFamily operations */
void ConcreteTrace::registerMadeSPFamily(Node * makerNode,FamilyID id,RootOfFamily esrRoot)
{
  getMadeSPFamilies(makerNode)->registerFamily(id,esrRoot);
}

void ConcreteTrace::unregisterMadeSPFamily(Node * makerNode,FamilyID id)
{
  getMadeSPFamilies(makerNode)->unregisterFamily(id);
}

bool ConcreteTrace::containsMadeSPFamily(Node * makerNode, FamilyID id) { assert(false); }
RootOfFamily ConcreteTrace::getMadeSPFamilyRoot(Node * makerNode, FamilyID id) { assert(false); }


/* New in ConcreteTrace */

BlockID ConcreteTrace::sampleBlock(ScopeID scope) { assert(false); }
double ConcreteTrace::logDensityOfBlock(ScopeID scope) { assert(false); }
vector<BlockID> ConcreteTrace::blocksInScope(ScopeID scope) { assert(false); }
int ConcreteTrace::numBlocksInScope(ScopeID scope) { assert(false); }
set<Node*> ConcreteTrace::getAllNodesInScope(ScopeID scope) { assert(false); }
    
vector<set<Node*> > ConcreteTrace::getOrderedSetsInScope(ScopeID scope) { assert(false); }

set<Node*> ConcreteTrace::getNodesInBlock(ScopeID scope, BlockID block) { assert(false); }

void ConcreteTrace::addUnconstrainedChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node) { assert(false); }

bool ConcreteTrace::scopeHasEntropy(ScopeID scope) { assert(false); }
void ConcreteTrace::makeConsistent() { assert(false); }


int ConcreteTrace::numUnconstrainedChoices() { assert(false); }

int ConcreteTrace::getSeed() { assert(false); }
double ConcreteTrace::getGlobalLogScore() { assert(false); }

//void ConcreteTrace::addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies) { assert(false); }
//void ConcreteTrace::addNewChildren(Node * node,PSet newChildren) { assert(false); }
