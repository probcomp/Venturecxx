#include "concrete_trace.h"
#include "values.h"

/* Constructor */

ConcreteTrace::ConcreteTrace()
{
  map<string,VentureValuePtr> builtInValues = initBuiltInValues();
  map<string,shared_ptr<VentureSP> > builtInSPs = initBuiltInSPs();

  for (map<string,VentureValuePtr>::iterator iter = builtInValues.begin();
       iter != builtInValues.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym = new VentureSymbol(iter->first);
    ConstantNode * node = createConstantNode(iter->second);
    globalEnv->addBinding(sym,node);
  }

  for (map<string,shared_ptr<VentureSP> >::iterator iter = builtInSPs.begin();
       iter != builtInSPs.end();
       ++iter)
  {
    shared_ptr<VentureSymbol> sym = new VentureSymbol(iter->first);
    ConstantNode * node = createConstantNode(iter->second);
    processMadeSP(this,node,false);
    globalEnv->addBinding(sym,node);
  }
}



/* Registering metadata */
void ConcreteTrace::registerAEKernel(Node * node) { throw 500; }

void ConcreteTrace::registerUnconstrainedChoice(Node * node) {
  assert(unconstrainedChoices.count(node) == 0);
  unconstrainedChoices.insert(node);
}

void ConcreteTrace::registerUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) { throw 500; }

void ConcreteTrace::registerConstrainedChoice(Node * node) {
  assert(constrainedChoices.count(node) == 0);
  constrainedChoices.insert(node);
}

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) { throw 500; }

void ConcreteTrace::unregisterUnconstrainedChoice(Node * node) {
  assert(unconstrainedChoices.count(node) == 1);
  unconstrainedChoices.erase(node);
}

void ConcreteTrace::unregisterUnconstrainedChoiceInScope(ScopeID scope,BlockID block,Node * node) { throw 500; }

void ConcreteTrace::unregisterConstrainedChoice(Node * node) {
  assert(constrainedChoices.count(node) == 1);
  constrainedChoices.erase(node);
}

/* Regen mutations */
void ConcreteTrace::addESREdge(Node *esrParent,OutputNode * outputNode) { throw 500; }
void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) { throw 500; }
void ConcreteTrace::incNumRequests(Node * node) { throw 500; }
void ConcreteTrace::addChild(Node * node, Node * child) {
  assert(children[node].count(child) == 0);
  children[node].insert(child);
}

/* Detach mutations */  
Node * ConcreteTrace::popLastESRParent(OutputNode * outputNode) { throw 500; }
void ConcreteTrace::disconnectLookup(LookupNode * lookupNode) { throw 500; }
void ConcreteTrace::decNumRequests(Node * node) { throw 500; }
void ConcreteTrace::removeChild(Node * node, Node * child) { throw 500; }

/* Primitive getters */
VentureValuePtr ConcreteTrace::getValue(Node * node) {
  return values[node];
}

SPRecord ConcreteTrace::getMadeSPRecord(OutputNode * makerNode) {
  return madeSPRecords[makerNode];
}

vector<Node*> ConcreteTrace::getESRParents(Node * node) {
  return esrParents[node];
}

set<Node*> ConcreteTrace::getChildren(Node * node) {
  return children[node];
}

int ConcreteTrace::getNumRequests(Node * node) {
  return numRequests[node];
}

int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { throw 500; }

VentureValuePtr ConcreteTrace::getObservedValue(Node * node) {
  return observedValues[node];
}

bool ConcreteTrace::isConstrained(Node * node) {
  return constrainedChoices.count(node);
}

bool ConcreteTrace::isObservation(Node * node) {
  return observedValues.count(node);
}

/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) {
  values[node] = value;
}

void ConcreteTrace::clearValue(Node * node) {
  values.erase(node);
}

void ConcreteTrace::createSPRecord(OutputNode * makerNode) { throw 500; }

void ConcreteTrace::initMadeSPFamilies(Node * node) { throw 500; }
void ConcreteTrace::clearMadeSPFamilies(Node * node) { throw 500; }

void ConcreteTrace::setMadeSP(Node * node,shared_ptr<VentureSP> sp) { throw 500; }
void ConcreteTrace::setMadeSPAux(Node * node,shared_ptr<SPAux> spaux) { throw 500; }

void ConcreteTrace::setChildren(Node * node,set<Node*> children) { throw 500; }
void ConcreteTrace::setESRParents(Node * node,const vector<Node*> & esrParents) { throw 500; }

void ConcreteTrace::setNumRequests(Node * node,int num) { throw 500; }

/* SPFamily operations */
void ConcreteTrace::registerMadeSPFamily(OutputNode * makerNode, FamilyID id, Node * esrParent) { throw 500; }
void ConcreteTrace::unregisterMadeSPFamily(OutputNode * maderNode, FamilyID id, Node * esrParent) { throw 500; }
bool ConcreteTrace::containsMadeSPFamily(OutputNode * makerNode, FamilyID id) { throw 500; }
Node * ConcreteTrace::getMadeSPFamilyRoot(OutputNode * makerNode, FamilyID id) { throw 500; }


/* New in ConcreteTrace */

BlockID ConcreteTrace::sampleBlock(ScopeID scope) { throw 500; }
double ConcreteTrace::logDensityOfBlock(ScopeID scope) { throw 500; }
vector<BlockID> ConcreteTrace::blocksInScope(ScopeID scope) { throw 500; }
int ConcreteTrace::numBlocksInScope(ScopeID scope) { throw 500; }
set<Node*> ConcreteTrace::getAllNodesInScope(ScopeID scope) { throw 500; }
    
vector<set<Node*> > ConcreteTrace::getOrderedSetsInScope(ScopeID scope) { throw 500; }

set<Node*> ConcreteTrace::getNodesInBlock(ScopeID scope, BlockID block) { throw 500; }

void ConcreteTrace::addUnconstrainedChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node) { throw 500; }

bool ConcreteTrace::scopeHasEntropy(ScopeID scope) { throw 500; }
void ConcreteTrace::makeConsistent() { throw 500; }
Node * ConcreteTrace::getOutermostNonRefAppNode(Node * node) { throw 500; }

int ConcreteTrace::numUnconstrainedChoices() { throw 500; }

int ConcreteTrace::getSeed() { throw 500; }
double ConcreteTrace::getGlobalLogScore() { throw 500; }

//void ConcreteTrace::addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies) { throw 500; }
//void ConcreteTrace::addNewChildren(Node * node,PSet newChildren) { throw 500; }
