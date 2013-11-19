#include "particle.h"
#include "node.h"
#include "sp.h"
#include "spaux.h"
#include "value.h"

VentureSP * Particle::vsp(Node * node)
{
  VentureSP * _vsp = dynamic_cast<VentureSP*>(getValue(node->operatorNode));
  assert(_vsp);
  return _vsp;
}

void Particle::maybeCloneSPAux(Node * node)
{
  Node * makerNode = vsp(node)->makerNode;
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void Particle::maybeCloneMadeSPAux(Node * makerNode)
{
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void Particle::registerSPAux(Node * makerNode,SPAux * freshSPAux)
{
  assert(!spauxs.count(makerNode));
  spauxs[makerNode] = freshSPAux;
}

SPAux * Particle::getSPAux(Node * node)
{
  if (!sp(node)->hasAux()) { return nullptr; }
  assert(spauxs.count(vsp(node)->makerNode));
  return spauxs[vsp(node)->makerNode];
}

SPAux * Particle::getMadeSPAux(Node * makerNode)
{
  assert(spauxs.count(makerNode));
  return spauxs[makerNode];
}

SP * Particle::sp(Node * node)
{
  VentureValue * op = getValue(node->operatorNode);
  VentureSP * vsp = dynamic_cast<VentureSP*>(op);
  assert(vsp);
  return vsp->sp;
}

void Particle::registerReference(Node * node,Node * lookedUpNode)
{
  children.insert({lookedUpNode,node});
  lookedUpNodes[node] = lookedUpNode;
  if (isReference(lookedUpNode))
  {
    sourceNodes[node] = getSourceNode(lookedUpNode);
  }
  else
  {
    sourceNodes[node] = lookedUpNode;
  }
}

bool Particle::isReference(Node * node)
{
  return sourceNodes.count(node);
}


// TODO URGENT this is so freaking subtle
// what if the lookedUpNode is already in the trace in
// registerReference?
// (I think this works correctly)
Node * Particle::getSourceNode(Node * node)
{
  assert(node);
  if (sourceNodes.count(node))
  { 
    assert(sourceNodes.count(node));
    return sourceNodes[node];
  }
  else 
  { 
    assert(node->sourceNode);
    return node->sourceNode; 
  }
}

/* Depends on subtle invariants. We only query values that are owned by the particle,
   which recursively may query source nodes that already have values. If there is a
   weird bug in this program, reconsider this method more carefully. 
   TODO URGENT: in order to handle multiple levels, this is the one place where we need
   to implement environment-lookup semantics. In order to only do so when actually necessary,
   we need to have a global collection of all nodes in ancestor maps.*/
VentureValue * Particle::getValue(Node * node)
{
  if (isReference(node)) { return getValue(getSourceNode(node)); }
  if (values.count(node)) { return values[node]; }
  return node->getValue();
}
 
void Particle::setValue(Node * node, VentureValue * value, bool override)
{
  if (values.count(node))
  {
    if (override) { values[node] = value; }
  }
  else { values[node] = value; }
}

bool Particle::hasValueFor(Node * node)
{
  return values.count(node);
}

void Particle::unregisterRandomChoice(Node * node)
{
  assert(randomChoices.count(node));
  randomChoices.erase(node);
}

void Particle::registerConstrainedChoice(Node * node)
{
  constrainedChoices.insert(node);
}

void Particle::registerRandomChoice(Node * node)
{
  randomChoices.insert(node);
}

void Particle::unregisterConstrainedChoice(Node * node)
{
  assert(constrainedChoices.count(node));
  constrainedChoices.erase(node);
}

Args Particle::makeArgs(Node * node)
{
  Args args;
  
  for (Node * operandNode : node->operandNodes)
  { args.operands.push_back(getValue(operandNode)); }
  args.operandNodes = node->operandNodes;

  if (node->requestNode) { args.request = getValue(node->requestNode); }
  args.requestNode = node->requestNode;
  args.outputNode = node->outputNode;

  for (Node * esrNode : esrParents[node])
  {
    args.esrs.push_back(getValue(esrNode));
  }
  args.esrNodes = esrParents[node];

  args.spaux = getSPAux(node);

//  args.madeSPAux = getMadeSPAux(node);
  args.familyEnv = node->familyEnv;
  args.nodeType = node->nodeType;

  return args;
}
