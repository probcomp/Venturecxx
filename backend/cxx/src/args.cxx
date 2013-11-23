#include "args.h"
#include "node.h"
#include "trace.h"
#include "value.h"

vector<VentureValue *> makeVectorOfValues(Trace * trace, const vector<Node*> & nodes)
{
  vector<VentureValue *> values;
  for (Node * node : nodes) 
  { 
    VentureValue * value = trace->getValue(node);
    if (!value)
    {
      cout << "NULL Argument @ " << node->address << endl;
    }
    assert(value);
    assert(value->isValid());
    values.push_back(value);
  }
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
