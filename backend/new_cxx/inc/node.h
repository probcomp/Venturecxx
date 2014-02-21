#ifndef NODE_H
#define NODE_H

#include "types.h"

struct VentureEnvironment;

struct Node
{
  vector<Node*> definiteParents; // TODO should be an iterator
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
  ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env);
  Node * operatorNode;
  vector<Node *> operandNodes;
  shared_ptr<VentureEnvironment> env;
};

struct OutputNode;

struct RequestNode : ApplicationNode
{
  RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env);
  OutputNode * outputNode;
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env);
  RequestNode * requestNode;
};

#endif
