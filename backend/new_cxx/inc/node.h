#ifndef NODE_H
#define NODE_H

#include <boost/shared_ptr.hpp>
#include <set>
#include <vector>

struct Node
{
  boost::shared_ptr<VentureValue> value;
  std::vector<Node*> definiteParents{};
};

struct ConstantNode : Node { ConstantNode(boost::shared_ptr<VentureValue> value); };
struct LookupNode : Node { LookupNode(Node * sourceNode); };
struct ApplicationNode : Node;
struct RequestNode : ApplicationNode
{
  RequestNode(Node * operatorNode,std::vector<Node*> operandNodes, VentureEnvironment * env);
};

struct OutputNode : ApplicationNode
{
  OutputNode(Node * operatorNode,std::vector<Node*> operandNodes,Node * requestNode,VentureEnvironment * env);
};
