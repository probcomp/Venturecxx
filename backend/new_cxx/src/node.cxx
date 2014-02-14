#include "node.h"

LookupNode::LookupNode(Node * sourceNode) :
  sourceNode(sourceNode)
  {
    definiteParents.push_back(sourceNode);
  }

ApplicationNode::ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env)
{
  definiteParents.push_back(operatorNode);
  for (size_t i = 0; i < operandNodes.size(); ++i) { definiteParents.push_back(operandNodes[i]); }
}

RequestNode::RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env)
  { }

OutputNode::OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env),
  requestNode(requestNode)
{
  definiteParents.push_back(requestNode);
}
