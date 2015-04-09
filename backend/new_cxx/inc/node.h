// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

#ifndef NODE_H
#define NODE_H

#include "types.h"

struct VentureEnvironment;

struct Node
{
  Node(VentureValuePtr exp): exp(exp) {}
  virtual vector<Node*> getDefiniteParents() { return vector<Node*>(); } // TODO should be an iterator
  set<Node*> children; // particle stores NEW children
  virtual ~Node() {} // TODO destroy family
  VentureValuePtr exp;
  virtual Node* copy_help(ForwardingMap* m) const =0;
};

struct ConstantNode : Node 
{
  ConstantNode(VentureValuePtr exp): Node(exp) {}
  ConstantNode* copy_help(ForwardingMap* m) const;
};

struct LookupNode : Node 
{ 
  LookupNode(Node * sourceNode, VentureValuePtr exp);
  vector<Node*> getDefiniteParents() { vector<Node*> dps; dps.push_back(sourceNode); return dps; }
  Node * sourceNode;
  LookupNode* copy_help(ForwardingMap* m) const;
};

struct ApplicationNode : Node
{
  ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp);
  Node * operatorNode;
  vector<Node *> operandNodes;
  shared_ptr<VentureEnvironment> env;
};

struct OutputNode;

struct RequestNode : ApplicationNode
{
  RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env);
  vector<Node*> getDefiniteParents();
  OutputNode * outputNode;
  RequestNode* copy_help(ForwardingMap* m) const;
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp);
  vector<Node*> getDefiniteParents();
  RequestNode * requestNode;
  bool isFrozen;
  ~OutputNode();
  OutputNode* copy_help(ForwardingMap* m) const;
};

#endif
