#include "particle.h"
#include "trace.h"
#include "node.h"
#include "value.h"

// map<Node *, ParticleNode> pnodes;
// map<Node *, vector<Node *> > children;
// map<Node*,SPAux*> spauxs;

// set<Node *> randomChoices;
// set<Node *> constrainedChoices;

// queue<FlushEntry> flushQueue;
// set<Node *> random

// Trace * trace{nullptr};

bool DetachParticle::isReference(Node * node) { return trace->isReference(node); }
void DetachParticle::registerReference(Node * node, Node * lookedUpNode) { assert(false); }
Node * DetachParticle::getSourceNode(Node * node) { assert(false); }
void DetachParticle::setSourceNode(Node * node, Node * sourceNode) { trace->setSourceNode(node,sourceNode); }
void DetachParticle::clearSourceNode(Node * node) 
{ 
  pnodes[node] = ParticleNode(
  trace->clearSourceNode(node); }

void DetachParticle::setValue(Node * node, VentureValue * value) { trace->s
void DetachParticle::clearValue(Node * node);
VentureValue * DetachParticle::getValue(Node * node);

SP * DetachParticle::getSP(Node * node);
VentureSP * DetachParticle::getVSP(Node * node);
SPAux * DetachParticle::getSPAux(Node * node);
SPAux * DetachParticle::getMadeSPAux(Node * makerNode);
Args DetachParticle::getArgs(Node * node);
vector<Node *> DetachParticle::getESRParents(Node * node);
  
void DetachParticle::constrainChoice(Node * node);
void DetachParticle::unconstrainChoice(Node * node);

void DetachParticle::setConstrained(Node * node,bool isConstrained);
void DetachParticle::setNodeOwnsValue(Node * node,bool giveOwnershipToSP);

Node * DetachParticle::removeLastESREdge(Node * outputNode);
void DetachParticle::addESREdge(Node * esrParent,Node * outputNode);

void DetachParticle::disconnectLookup(Node * node);

void DetachParticle::preUnabsorb(Node * node) {}
void DetachParticle::preAbsorb(Node * node) {}
void DetachParticle::preUnapplyPSP(Node * node) {}
void DetachParticle::preApplyPSP(Node * node) {}
void DetachParticle::preUnevalRequests(Node * requestNode) {}
void DetachParticle::preEvalRequests(Node * requestNode) {}
void DetachParticle::preUnconstrain(Node * node) {}
void DetachParticle::preConstrain(Node * node) {}

void DetachParticle::extractLatentDB(SP * sp,LatentDB * latentDB);
void DetachParticle::registerGarbage(SP * sp,VentureValue * value,NodeType nodeType);
void DetachParticle::extractValue(Node * node, VentureValue * value);
void DetachParticle::prepareLatentDB(SP * sp);
LatentDB * DetachParticle::getLatentDB(SP * sp);
void DetachParticle::processDetachedLatentDB(SP * sp, LatentDB * latentDB);

void DetachParticle::registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values);
void DetachParticle::registerSPFamily(Node * makerNode,size_t id,Node * root);
