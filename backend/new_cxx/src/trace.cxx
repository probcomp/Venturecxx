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

/* Derived getters */

VentureValuePtr getGroundValue(Node * node)
{
  VentureValuePtr value = getValue(node);
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  
  if (spRef) { return getValue(spRef->makerNode); }
  else { return value; }
}

Node * getOperatorSPMakerNode(ApplicationNode * node)
{
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(getValue(node->operatorNode));
  assert(spRef);
  return spRef->makerNode;
}

shared_ptr<VentureSP> getMadeSP(Node * makerNode)
{
  SPRecord spRecord = getMadeSPRecord(node);
  return spRecord.sp;
}

shared_ptr<SPFamilies> getMadeSPFamilies(Node * makerNode)
{
  SPRecord spRecord = getMadeSPRecord(node);
  return spRecord.spFamilies;
}

shared_ptr<SPAux> getMadeSPAux(Node * makerNode)
{
  SPRecord spRecord = getMadeSPRecord(node);
  return spRecord.spAux;
}

vector<Node*> getParents(Node * node)
{
  vector<Node*> parents = node->definiteParents;
  if (dynamic_cast<OutputNode*>(node)) 
  {
    vector<Node*> esrParents = getESRParents(node);
    parents.insert(definiteParents.end(),esrParents.begin(),esrParents.end());
  }
  return parents;
}
