#include<memory>

ConstantNode * Trace::createConstantNode(VentureValuePtr value)
{
  ConstantNode * constantNode = new ConstantNode();
  setValue(constantNode, value);
  return constantNode;
}

LookupNode * Trace::createLookupNode(Node * sourceNode)
{
  LookupNode * lookupNode = new LookupNode(sourceNode);
  setValue(lookupNode,getValue(sourceNode));
  addChild(sourceNode,lookupNode);
  return lookupNode;
}


pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env)
{
  RequestNode * requestNode = new RequestNode(operatorNode, operandNodes, env);
  OutputNode * outputNode = new OutputNode(operatorNode, operandNodes, requestNode, env);
  
  requestNode.outputNode = outputNode;
  addChild(requestNode, outputNode);
  
  addChild(operatorNode, requestNode);
  addChild(operatorNode, outputNode);
  
  for (size_t i = 0; i < operandNodes.size(); ++i) {
    addChild(operandNodes[i], requestNode);
    addChild(operandNodes[i], outputNode);
  }
  
  return make_pair(requestNode, outputNode);
}

VentureValuePtr getGroundValue(Node * node)
{
  throw 500;

  VentureValuePtr value = getValue(node);
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  
  if (spRef) { return getMade(); }
  else { return value; }
}

Node * getSPMakerNode(Node * node) { throw 500; }
shared_ptr<SPRef> getSPRef(Node * node) { throw 500; }
shared_ptr<VentureSP> getSP(Node * node) { throw 500; }
shared_ptr<SPFamilies> getSPFamilies(Node * node) { throw 500; }
shared_ptr<SPAux> getSPAux(Node * node) { throw 500; }
shared_ptr<PSP> getPSP(Node * node) { throw 500; }
vector<Node*> getParents(Node * node) { throw 500; }
