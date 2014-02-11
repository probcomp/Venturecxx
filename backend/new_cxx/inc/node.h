#ifndef NODE_H
#define NODE_H

#include <boost/shared_ptr.hpp>
#include <set>
#include <vector>

struct Node
{
  std::vector<Node*> definiteParents; // TODO should be an iterator
  virtual ~Node() {} // TODO destroy family
};

struct ConstantNode : Node {};

struct LookupNode : Node 
{ 
  LookupNode(Node * sourceNode);
  Node * sourceNode;
};

struct ApplicationNode : Node
{
  Node * operatorNode;
  vector<Node *> operandNodes;
  shared_ptr<VentureEnvironment> env;
};

struct RequestNode : ApplicationNode
{
  RequestNode(Node * operatorNode, const std::vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env);
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode, const std::vector<Node*>& operandNodes, Node * requestNode, const shared_ptr<VentureEnvironment>& env);
  RequestNode * requestNode;
};
