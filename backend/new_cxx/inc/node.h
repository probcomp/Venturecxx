#ifndef NODE_H
#define NODE_H

#include "types.h"

struct VentureEnvironment;

struct Node
{
  Node(VentureValuePtr exp): exp(exp) {}
  vector<Node*> definiteParents; // TODO should be an iterator
  set<Node*> children; // particle stores NEW children
  virtual ~Node() {} // TODO destroy family
  VentureValuePtr exp;
};

struct ConstantNode : Node 
{
 ConstantNode(VentureValuePtr exp): Node(exp) {}
};

struct LookupNode : Node 
{ 
  LookupNode(Node * sourceNode, VentureValuePtr exp);
  Node * sourceNode;
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
  OutputNode * outputNode;
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp);
  RequestNode * requestNode;
  bool isFrozen;
  ~OutputNode();
};

#endif
