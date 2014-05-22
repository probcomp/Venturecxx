#include "node.h"
#include "values.h"

LookupNode::LookupNode(Node * sourceNode,VentureValuePtr exp) :
  Node(exp),
  sourceNode(sourceNode) {}

ApplicationNode::ApplicationNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  Node(exp),
  operatorNode(operatorNode),
  operandNodes(operandNodes),
  env(env) {}

RequestNode::RequestNode(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env) :
  ApplicationNode(operatorNode,operandNodes,env,VentureValuePtr(new VentureNil))
  { }

vector<Node*> RequestNode::getDefiniteParents()
{
  vector<Node*> dps;
  dps.push_back(operatorNode);
  dps.insert(dps.end(),operandNodes.begin(),operandNodes.end());
  return dps;
}

OutputNode::OutputNode(Node * operatorNode, const vector<Node*>& operandNodes, RequestNode * requestNode, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp) :
  ApplicationNode(operatorNode,operandNodes,env,exp),
  requestNode(requestNode),
  isFrozen(false) {}

vector<Node*> OutputNode::getDefiniteParents()
{
  vector<Node*> dps;
  dps.push_back(operatorNode);
  dps.insert(dps.end(),operandNodes.begin(),operandNodes.end());
  dps.push_back(requestNode);
  return dps;
}


OutputNode::~OutputNode()
{
  delete requestNode;
  for (size_t i = 0; i < operandNodes.size(); ++i) { delete operandNodes[i]; }
  delete operatorNode;
}
