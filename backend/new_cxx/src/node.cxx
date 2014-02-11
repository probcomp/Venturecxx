#include "node.h"

LookupNode::LookupNode(Node * sourceNode) :
  sourceNode(sourceNode)
  {}

RequestNode::RequestNode(Node * operatorNode, const std::vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env)
  {}

OutputNode::OutputNode(Node * operatorNode, const std::vector<Node*>& operandNodes, Node * requestNode, const share_ptr<VentureEnvironment>& env) :
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  requestNode(requestNode),
  env(env),
  {}
