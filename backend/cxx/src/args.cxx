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
  Args args;

  args.operands = makeVectorOfValues(node->operandNodes);
  args.operandNodes = node->operandNodes;

  if (node->requestNode)
  {
    args.request = node->requestNode->getValue();
    args.requestNode = node->requestNode;
  }

  args.esrs = makeVectorOfValues(node->esrParents);
  args.esrNodes = node->esrParents;

  args.spaux = node->spaux();
  args.familyEnv = node->familyEnv;
  
  return args;
}
