#include "node.h"

LookupNode::LookupNode(Node * sourceNode) :
  sourceNode(sourceNode)
  {}

ApplicationNode::ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env)
{}

RequestNode::RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env)
  {}

OutputNode::OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env),
  requestNode(requestNode)
{}
