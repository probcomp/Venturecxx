#include "node.h"
#include "values.h"

LookupNode::LookupNode(Node * sourceNode,VentureValuePtr exp) :
  Node(exp),
  sourceNode(sourceNode)
  {
    definiteParents.push_back(sourceNode);
  }

ApplicationNode::ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  Node(exp),
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env)
{
  definiteParents.push_back(operatorNode);
  for (size_t i = 0; i < operandNodes.size(); ++i) { definiteParents.push_back(operandNodes[i]); }
}

RequestNode::RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env,VentureValuePtr(new VentureNil))
  { }

OutputNode::OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  ApplicationNode(operatorNode,operandNodes,env,exp),
  requestNode(requestNode),
  isFrozen(false)
{
  definiteParents.push_back(requestNode);
}

OutputNode::~OutputNode()
{
  delete requestNode;
  for (size_t i = 0; i < operandNodes.size(); ++i) { delete operandNodes[i]; }
  delete operatorNode;
}
