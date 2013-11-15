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
  args.request = node->requestNode->getValue();
  args.esrs = makeVectorOfValues(node->esrParents);
  args.spaux = node->spaux();
}
