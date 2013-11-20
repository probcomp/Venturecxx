#include "args.h"
#include "node.h"
#include "trace.h"

vector<VentureValue *> makeVectorOfValues(Trace * trace, const vector<Node*> & nodes)
{
  vector<VentureValue *> values;
  for (Node * node : nodes) { values.push_back(trace->getValue(node)); }
  return values;
}

Args::Args(Trace * trace, Node * node)
{
  operands = makeVectorOfValues(trace,node->operandNodes);
  operandNodes = node->operandNodes;

  outputNode = node->outputNode;
  requestNode = node->requestNode;

  if (node->requestNode)
  {
    request = trace->getValue(node->requestNode);
  }

  esrs = makeVectorOfValues(trace,trace->getESRParents(node));
  esrNodes = trace->getESRParents(node);

  spaux = trace->getSPAux(node);
  madeSPAux = trace->getMadeSPAux(node);

  familyEnv = node->familyEnv;

  if (node->nodeType == NodeType::REQUEST) { isRequest = true; }
  
}
