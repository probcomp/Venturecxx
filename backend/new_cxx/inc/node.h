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
