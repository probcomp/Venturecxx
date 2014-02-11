#include "args.h"

vector<VentureValuePtr> makeVectorOfValues(const vector<Node*> & nodes)
{
  vector<VentureValuePtr> values;
  for (size_t i = 0; i < values.size(); i++)
  {
    values.push_back(trace->getValue(node));
  }
  return values;
}

Args::Args(Trace * trace, Node * appNode)
{
  node = appNode;
  operandValues = makeVectorOfValues(appNode->operandNodes);
  operandNodes = appNode->operandNodes;

  spAux = trace->getMadeSPAux(trace->getSPMakerNode(appNode));
  env = appNode->env;

  OutputNode * outputNode = dynamic_cast<OutputNode>(appNode);
  if (outputNode)
  {
    requestValue = dynamic_pointer_cast<VentureRequest>(trace->getValue(outputNode));
    assert(requestValue);
    requestNode = outputNode->requestNode;
    
    esrValues = makeVectorOfValues(trace->getESRParents(outputNode));
    esrNodes = trace->getESRParents(outputNode);
    madeSPAux = trace->getMadeSPAux(outputNode);
  }
}

