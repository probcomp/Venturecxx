#include "particle.h"
#include "node.h"
#include "spaux.h"

void Particle::maybeCloneSPAux(Node * node)
{
  Node * makerNode = node->vsp()->makerNode;
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void Particle::maybeCloneSPAux(Node * makerNode)
{
  if (makerNode->madeSPAux && !spauxs.count(makerNode))
  {
    spauxs[makerNode] = makerNode->madeSPAux->clone();
  }
}

void registerSPAux(Node * makerNode,SPAux * freshSPAux)
{
  assert(!spauxs.count(makerNode));
  spauxs[makerNode] = freshSPAux;
}

SPAux * getSPAux(Node * node)
{
  if (!sp(node)->hasAux()) { return nullptr; }
  assert(spauxs.count(node->vsp()->makerNode));
  return spauxs[node->vsp()->makerNode];
}

SPAux * getMadeSPAux(Node * makerNode)
{
  assert(spauxs.count(makerNode));
  return spauxs[makerNode];
}

SP * sp(Node * node)
{
  VentureValue * op = getValue(node->operatorNode);
  VentureSP * vsp = dynamic_cast<VentureSP*>(op);
  assert(vsp);
  return vsp->sp;
}

bool isReference(Node * node)
{
  return sourceNodes.count(node);
}

Node * getSourceNode(Node * node)
{
  assert(sourceNodes.count(node));
  return sourceNodes[node];
}

/* Depends on subtle invariants. We only query values that are owned by the particle,
   which recursively may query source nodes that already have values. If there is a
   weird bug in this program, reconsider this method more carefully. 
   TODO URGENT: in order to handle multiple levels, this is the one place where we need
   to implement environment-lookup semantics. In order to only do so when actually necessary,
   we need to have a global collection of all nodes in ancestor maps.*/
VentureValue * getValue(Node * node)
{
  if (isReference(node)) { return getValue(getSourceNode(node)); }
  if (values.count(node)) { return values[node]; }
  return node->getValue();
}
 
void setValue(Node * node, VentureValue * value)
{
  values[node] = value;
}

bool hasValueFor(Node * node)
{
  return values.count(node);
}

void unregisterRandomChoice(Node * node)
{
  assert(randomChoices.count(node));
  randomChoices.erase(node);
}

void registerConstrainedChoice(Node * node)
{
  constrainedChoices.insert(node);
}

Args makeArgs(Node * node)
{
  Args args(node);
  for (Node * operandNode : node->operandNodes)
  { args.operands.push_back(getValue(operandNode)); }

  if (node->requestNode) { args.request = getValue(node->requestNode); }

  for (Node * esrNode : esrParents[node])
  {
    args.esrs.push_back(getValue(esrNode));
  }
  args.esrNodes = esrParents[node];

  args.spaux = getSPAux(node);
  return args;
}
