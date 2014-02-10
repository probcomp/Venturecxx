ConstantNode::ConstantNode(boost::shared_ptr<VentureValue> value) { throw 500; }
LookupNode::LookupNode(Node * sourceNode) { throw 500; }
RequestNode::RequestNode(Node * operatorNode,std::vector<Node*> operandNodes, VentureEnvironment * env) { throw 500; }
OutputNode::OutputNode(Node * operatorNode,std::vector<Node*> operandNodes,Node * requestNode,VentureEnvironment * env) { throw 500; }
