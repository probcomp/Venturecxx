#include "node.h"


ConstantNode::ConstantNode(boost::shared_ptr<VentureValue> value) { throw 500; }
LookupNode::LookupNode(Node * sourceNode) { throw 500; }
RequestNode::RequestNode(Node * operatorNode,std::vector<Node*> operandNodes, shared_ptr<VentureEnvironment> env) { throw 500; }
OutputNode::OutputNode(Node * operatorNode,std::vector<Node*> operandNodes,Node * requestNode,shared_ptr<VentureEnvironment> env) 
{ throw 500; }
