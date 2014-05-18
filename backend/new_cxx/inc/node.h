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
  virtual Node* copy_help(ForwardingMap* m) =0;
};

struct ConstantNode : Node 
{
  ConstantNode(VentureValuePtr exp): Node(exp) {}
  ConstantNode* copy_help(ForwardingMap* m);
};

struct LookupNode : Node 
{ 
  LookupNode(Node * sourceNode, VentureValuePtr exp);
  Node * sourceNode;
  LookupNode* copy_help(ForwardingMap* m);
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
  RequestNode* copy_help(ForwardingMap* m);
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp);
  RequestNode * requestNode;
  ~OutputNode();
  OutputNode* copy_help(ForwardingMap* m);
};

#endif
