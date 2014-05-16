#ifndef NODE_H
#define NODE_H

#include "types.h"

struct VentureEnvironment;

struct Node
{
  Node(VentureValuePtr exp): exp(exp) {}
  vector<AddrPtr> definiteParents; // TODO should be an iterator
  set<AddrPtr> children; // particle stores NEW children
  virtual ~Node() {}
  VentureValuePtr exp;
};

struct ConstantNode : Node 
{
 ConstantNode(VentureValuePtr exp): Node(exp) {}
};

struct LookupNode : Node 
{ 
  LookupNode(AddrPtr sourceNode, VentureValuePtr exp);
  AddrPtr sourceNode;
};

struct ApplicationNode : Node
{
  ApplicationNode(AddrPtr operatorNode, const vector<AddrPtr>& operandNodes, const shared_ptr<VentureEnvironment>& env, VentureValuePtr exp);
  AddrPtr operatorNode;
  vector<AddrPtr> operandNodes;
  shared_ptr<VentureEnvironment> env;
};

struct OutputNode;

struct RequestNode : ApplicationNode
{
  RequestNode(AddrPtr operatorNode, const vector<AddrPtr>& operandNodes, const shared_ptr<VentureEnvironment>& env);
  AddrPtr outputNode;
};

struct OutputNode : ApplicationNode
{
  OutputNode(AddrPtr operatorNode, const vector<AddrPtr>& operandNodes, AddrPtr requestNode, const shared_ptr<VentureEnvironment>& env, VentureValuePtr exp);
  AddrPtr requestNode;
  ~OutputNode();
};

#endif
