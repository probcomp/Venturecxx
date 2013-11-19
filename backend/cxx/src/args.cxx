#include "args.h"
#include "node.h"

vector<VentureValue *> Args::makeVectorOfValues(const vector<Node*> & nodes)
{
  vector<VentureValue *> values;
  for (Node * node : nodes) { values.push_back(node->getValue()); }
  return values;
}

Args::Args(Node * node)
{
  operands = makeVectorOfValues(node->operandNodes);
  operandNodes = node->operandNodes;

  outputNode = node->outputNode;
  requestNode = node->requestNode;

  if (node->requestNode)
  {
    request = node->requestNode->getValue();
  }

  esrs = makeVectorOfValues(node->esrParents);
  esrNodes = node->esrParents;

  spaux = node->spaux();
  madeSPAux = node->madeSPAux;

  nodeType = node->nodeType;
  familyEnv = node->familyEnv;
  
}
