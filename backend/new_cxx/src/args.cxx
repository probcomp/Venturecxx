#include "args.h"
#include "trace.h"

vector<VentureValuePtr> makeVectorOfValues(Trace * trace, const vector<Node*> & nodes)
{
  vector<VentureValuePtr> values;
  for (size_t i = 0; i < nodes.size(); i++)
  {
    values.push_back(trace->getValue(nodes[i]));
  }
  return values;
}

vector<VentureValuePtr> makeVectorOfValues(Trace * trace, const vector<RootOfFamily> & nodes)
{
  vector<VentureValuePtr> values;
  for (size_t i = 0; i < nodes.size(); i++)
  {
    values.push_back(trace->getValue(nodes[i].get()));
  }
  return values;
}

Args::Args(Trace * trace, ApplicationNode * appNode)
{
  _trace = trace;
  node = appNode;

  operandNodes = node->operandNodes;
  operandValues = makeVectorOfValues(trace, operandNodes);

  spAux = trace->getMadeSPAux(trace->getOperatorSPMakerNode(appNode));
  env = node->env;

  OutputNode * outputNode = dynamic_cast<OutputNode*>(appNode);
  if (outputNode)
  {
    requestNode = outputNode->requestNode;
    requestValue = dynamic_pointer_cast<VentureRequest>(trace->getValue(requestNode));
    assert(requestValue);
    
    esrParentValues = makeVectorOfValues(trace, trace->getESRParents(outputNode));
    esrParentNodes = trace->getESRParents(outputNode);
    if (trace->hasAAAMadeSPAux(outputNode))
    {
      aaaMadeSPAux = trace->getAAAMadeSPAux(outputNode);
    }
  }
}

