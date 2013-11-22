#include <iostream>
#include <cassert>
#include <cstdlib>
#include <ctime>

#include "node.h"
#include "trace.h"
#include "builtin.h"
#include "sp.h"
#include "spaux.h"
#include "omegadb.h"
#include "flush.h"
#include "value.h"
#include "utils.h"
#include "env.h"

#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

Trace::Trace()
{
  gsl_rng_set (rng,time(NULL));
  
  primitivesEnv = new VentureEnvironment;
  for (pair<string,VentureValue *> p : initBuiltInValues()) 
  { primitivesEnv->addBinding(new VentureSymbol(p.first),new Node(Address(nullptr,0,p.first),NodeType::VALUE,p.second)); }

  for (pair<string,SP *> p : initBuiltInSPs())
  { 
    Node * spNode = new Node(Address(nullptr,0,p.first),NodeType::VALUE);
    spNode->setValue(new VentureSP(p.second));
    processMadeSP(spNode,false);
    primitivesEnv->addBinding(new VentureSymbol(p.first),spNode);
  }

  globalEnv = new VentureEnvironment(primitivesEnv);

}

Trace::~Trace()
{

  setOptions(false,new OmegaDB);
  for (map<size_t, pair<Node *,VentureValue*> >::reverse_iterator iter = ventureFamilies.rbegin(); 
       iter != ventureFamilies.rend();
       ++iter)
  { 
    Node * root = iter->second.first;
    if (root->isObservation()) 
    { 
      unconstrain(root,true); 
    }
    detachVentureFamily(root); 
    destroyExpression(iter->second.second);
    destroyFamilyNodes(root);
  }

  flushDB(omegaDB,false);
  omegaDB = nullptr;

  globalEnv->destroySymbols();
  delete globalEnv;

  for (pair<string,Node*> p : primitivesEnv->frame)
  {
    Node * node = p.second;

    if (dynamic_cast<VentureSP*>(node->getValue()))
    { teardownMadeSP(node,false); }

    delete node->getValue();
    delete node;
  }
  primitivesEnv->destroySymbols();
  delete primitivesEnv;

  for (pair< pair<string,bool >, uint32_t> pp : callCounts)
  {
    assert(callCounts[make_pair(pp.first.first,false)] == callCounts[make_pair(pp.first.first,true)]);
  }



  gsl_rng_free(rng);

}

void Trace::addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes,Node * requestNode, Node * outputNode)
{
  Node::addOperatorEdge(operatorNode,requestNode);
  Node::addOperatorEdge(operatorNode,outputNode);

  Node::addOperandEdges(operandNodes, requestNode);
  Node::addOperandEdges(operandNodes, outputNode);

  Node::addRequestEdge(requestNode, outputNode);
}


////////////////////////////////

bool Trace::isReference(Node * node)
{
  return node->sourceNode != nullptr;
}

void Trace::registerReference(Node * node, Node * lookedUpNode) 
{ 
  assert(node->_value == nullptr);
  if (isReference(lookedUpNode))
    {
      setSourceNode(node, getSourceNode(lookedUpNode));
    }
  else
    {
      setSourceNode(node,lookedUpNode);
    }
}

Node * Trace::getSourceNode(Node * node) { return node->sourceNode; }
void Trace::setSourceNode(Node * node, Node * sourceNode) { node->sourceNode = sourceNode; }
void Trace::clearSourceNode(Node * node) { node->sourceNode = nullptr; }

void Trace::setValue(Node * node, VentureValue * value) { node->_value = value; }
void Trace::clearValue(Node * node) { node->_value = nullptr; }

VentureValue * Trace::getValue(Node * node)
{
  if (isReference(node))
  {
    assert(node->sourceNode);
    assert(!isReference(node->sourceNode));
    return getValue(node->sourceNode);
  }
  else
  {
    return node->_value;
  }
}

VentureSP * Trace::getVSP(Node * node)
{
  VentureSP * _vsp = dynamic_cast<VentureSP*>(getValue(node->operatorNode));
  assert(_vsp);
  return _vsp;
}

SP * Trace::getSP(Node * node)
{
  return getVSP(node)->sp;
}
 
SPAux * Trace::getSPAux(Node * node)
{
  return getVSP(node)->makerNode->madeSPAux;
}

SPAux * Trace::getMadeSPAux(Node * makerNode)
{
  return makerNode->madeSPAux;
}

Args Trace::getArgs(Node * node) { return Args(this,node); }

vector<Node *> Trace::getESRParents(Node * node)
{
  return node->esrParents;
}

void Trace::unconstrainChoice(Node * node)
{
  unregisterConstrainedChoice(node);
  registerRandomChoice(node);
}

void Trace::constrainChoice(Node * node)
{
  unregisterRandomChoice(node);
  registerConstrainedChoice(node);
}

void Trace::setConstrained(Node * node) { node->isConstrained = true; }
void Trace::clearConstrained(Node * node) { node->isConstrained = false; }

void Trace::setNodeOwnsValue(Node * node) { node->spOwnsValue = true; }
void Trace::clearNodeOwnsValue(Node * node) { node->spOwnsValue = false; }

Node * Trace::removeLastESREdge(Node * outputNode)
{
  vector<Node *> & esrParents = outputNode->esrParents;
  assert(!esrParents.empty());
  Node * esrParent = esrParents.back();
  assert(esrParent);
  esrParent->children.erase(outputNode);
  esrParent->numRequests--;
  esrParents.pop_back();
  return esrParent;
}

void Trace::addESREdge(Node * esrParent,Node * outputNode)
{
  esrParent->children.insert(outputNode);

  outputNode->esrParents.push_back(esrParent);
  esrParent->numRequests++;
}


void Trace::extractLatentDB(SP * sp,LatentDB * latentDB)
{
  assert(!omegaDB->latentDBs.count(sp));
  omegaDB->latentDBs.insert({sp,latentDB});
}
 
void Trace::registerGarbage(SP * sp,VentureValue * value,NodeType nodeType)
{
  omegaDB->flushQueue.emplace(sp,value,nodeType); 
}

void Trace::extractValue(Node * node, VentureValue * value)
{
  omegaDB->drgDB[node] = value;  
}

void Trace::prepareLatentDB(SP * sp)
{
  if (!omegaDB->latentDBs.count(sp))
  {
    omegaDB->latentDBs[sp] = sp->constructLatentDB(); 
  }
}
 
LatentDB * Trace::getLatentDB(SP * sp)
{
  return omegaDB->latentDBs[sp];
}
 
void Trace::processDetachedLatentDB(SP * sp, LatentDB * latentDB)
{
  // do nothing for omegaDB, maybe destroy it for particles
}

void Trace::registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values)
{
  omegaDB->spOwnedValues[make_pair(makerNode,id)] = values; 
}


void Trace::registerSPFamily(Node * makerNode,size_t id,Node * root)
{
  omegaDB->spFamilyDBs[{makerNode,id}] = root;
}

void Trace::setOptions(bool shouldRestore, OmegaDB * omegaDB)
{
  this->shouldRestore = shouldRestore;
  this->omegaDB = omegaDB;
}

void Trace::detachMadeSPAux(Node * makerNode)
{
  delete makerNode->madeSPAux; 
  makerNode->madeSPAux = nullptr;
}

void Trace::disconnectLookup(Node * node)
{
  node->lookedUpNode->children.erase(node);
}

void Trace::reconnectLookup(Node * node)
{
  node->lookedUpNode->children.insert(node);
}

void Trace::connectLookup(Node * node, Node * lookedUpNode)
{
  lookedUpNode->children.insert(node);
  node->lookedUpNode = lookedUpNode;
}
