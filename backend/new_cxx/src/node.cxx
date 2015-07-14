// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

#include "node.h"
#include "values.h"

LookupNode::LookupNode(Node * sourceNode,VentureValuePtr exp) :
  Node(exp),
  sourceNode(sourceNode) {}

ApplicationNode::ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const boost::shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  Node(exp),
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env) {}

RequestNode::RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const boost::shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env,VentureValuePtr(new VentureNil))
  { }

vector<Node*> RequestNode::getDefiniteParents()
{
  vector<Node*> dps;
  dps.push_back(operatorNode);
  dps.insert(dps.end(),operandNodes.begin(),operandNodes.end());
  return dps;
}

OutputNode::OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const boost::shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  ApplicationNode(operatorNode,operandNodes,env,exp),
  requestNode(requestNode),
  isFrozen(false) {}

vector<Node*> OutputNode::getDefiniteParents()
{
  vector<Node*> dps;
  dps.push_back(operatorNode);
  dps.insert(dps.end(),operandNodes.begin(),operandNodes.end());
  dps.push_back(requestNode);
  return dps;
}


OutputNode::~OutputNode()
{
  delete requestNode;
  for (size_t i = 0; i < operandNodes.size(); ++i) { delete operandNodes[i]; }
  delete operatorNode;
}
