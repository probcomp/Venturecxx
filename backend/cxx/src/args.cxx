#include "args.h"
#include "node.h"
#include "trace.h"

vector<VentureValue *> Args::makeVectorOfValues(const vector<Node*> & nodes)
{
  vector<VentureValue *> values;
  for (Node * node : nodes) { values.push_back(node->getValue()); }
  return values;
}

Args::Args(Trace * trace, Node * node)
{
  operands = makeVectorOfValues(node->operandNodes);
  operandNodes = node->operandNodes;

  outputNode = node->outputNode;
  requestNode = node->requestNode;

  if (node->requestNode)
  {
    request = trace->getValue(node->requestNode);
  }

  // TODO will become trace->esrParents(node)
  esrs = makeVectorOfValues(node->esrParents);
  esrNodes = node->esrParents;

  spaux = trace->getSPAux(node);
  madeSPAux = trace->getMadeSPAux(node);

  familyEnv = node->familyEnv;

  if (node->nodeType == NodeType::REQUEST) { isRequest = true; }
  
}
