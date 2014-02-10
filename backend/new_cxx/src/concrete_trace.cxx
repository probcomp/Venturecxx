
/* Registering metadata */
void ConcreteTrace::registerAEKernel(Node * node) { throw 500; }
void ConcreteTrace::registerRandomChoice(Node * node) { throw 500; }
void ConcreteTrace::registerRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) { throw 500; }
void ConcreteTrace::registerConstrainedChoice(Node * node) { throw 500; }

/* Unregistering metadata */
void ConcreteTrace::unregisterAEKernel(Node * node) { throw 500; }
void ConcreteTrace::unregisterRandomChoice(Node * node) { throw 500; }
void ConcreteTrace::unregisterRandomChoiceInScope(ScopeID scope,BlockID block,Node * node) { throw 500; }
void ConcreteTrace::unregisterConstrainedChoice(Node * node) { throw 500; }

/* Regen mutations */
void ConcreteTrace::addESREdge(Node *esrParent,OutputNode * outputNode) { throw 500; }
void ConcreteTrace::reconnectLookup(LookupNode * lookupNode) { throw 500; }
void ConcreteTrace::incNumRequests(Node * node) { throw 500; }
void ConcreteTrace::addChild(Node * node, Node * child) { throw 500; }

/* Detach mutations */  
Node * ConcreteTrace::popLastESRParent(OutputNode * outputNode) { throw 500; }
void ConcreteTrace::disconnectLookup(LookupNode * lookupNode) { throw 500; }
void ConcreteTrace::decNumRequests(Node * node) { throw 500; }
def ConcreteTrace::removeChild(Node * node, Node * child) { throw 500; }

/* Primitive getters */
VentureValuePtr ConcreteTrace::getValue(Node * node) { throw 500; }
SPRecord ConcreteTrace::getMadeSPRecord(OutputNode * makerNode) { throw 500; }
vector<Node*> ConcreteTrace::getESRParents(Node * node) { throw 500; }
set<Node*> ConcreteTrace::getChildren(Node * node) { throw 500; }
int ConcreteTrace::getNumRequests(Node * node) { throw 500; }
int ConcreteTrace::getRegenCount(shared_ptr<Scaffold> scaffold,Node * node) { throw 500; }
VentureValuePtr ConcreteTrace::getObservedValue(Node * node) { throw 500; }

bool ConcreteTrace::isConstrained(Node * node) { throw 500; }
bool ConcreteTrace::isObservation(Node * node) { throw 500; }

/* Primitive Setters */
void ConcreteTrace::setValue(Node * node, VentureValuePtr value) { throw 500; }
void ConcreteTrace::clearValue(Node * node) { throw 500; }

void ConcreteTrace::createSPRecord(OutputNode * makerNode) { throw 500; } // No analogue in VentureLite

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

void ConcreteTrace::addRandomChoicesInBlock(ScopeID scope, BlockID block,set<Node*> & pnodes,Node * node) { throw 500; }

bool ConcreteTrace::scopeHasEntropy(ScopeID scope) { throw 500; }
void ConcreteTrace::makeConsistent() { throw 500; }
Node * ConcreteTrace::getOutermostNonRefAppNode(Node * node) { throw 500; }

int ConcreteTrace::numRandomChoices() { throw 500; }

int ConcreteTrace::getSeed() { throw 500; }
double ConcreteTrace::getGlobalLogScore() { throw 500; }

void ConcreteTrace::addNewMadeSPFamilies(Node * node, PMap newMadeSPFamilies) { throw 500; }
void ConcreteTrace::addNewChildren(Node * node,PSet newChildren) { throw 500; }
