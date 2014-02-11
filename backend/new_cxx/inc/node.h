#ifndef NODE_H
#define NODE_H

#include <boost/shared_ptr.hpp>
#include <set>
#include <vector>
#include "types.h"

struct VentureEnvironment;

struct Node
{
  //boost::shared_ptr<VentureValue> value;
  std::vector<Node*> definiteParents; // TODO should be an iterator
  virtual ~Node() {} // TODO destroy family
};

struct ConstantNode : Node { ConstantNode(boost::shared_ptr<VentureValue> value); };

struct LookupNode : Node 
{ 
  LookupNode(Node * sourceNode); 
  Node * sourceNode;
};

struct ApplicationNode : Node
{
  Node * operatorNode;
  vector<Node *> operandNodes;
};

struct RequestNode : ApplicationNode
{
  RequestNode(Node * operatorNode,std::vector<Node*> operandNodes, shared_ptr<VentureEnvironment> env);
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode,std::vector<Node*> operandNodes,Node * requestNode,shared_ptr<VentureEnvironment> env);
  RequestNode * requestNode;
};

#endif
