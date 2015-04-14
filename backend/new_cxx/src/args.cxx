// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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

