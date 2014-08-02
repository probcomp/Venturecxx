#include "trace.h"
#include "sp.h"
#include "sprecord.h"
#include "args.h"
#include "sps/scope.h"

ConstantNode * Trace::createConstantNode(VentureValuePtr value)
{
  ConstantNode * constantNode = new ConstantNode(value);
  setValue(constantNode, value);
  return constantNode;
}

LookupNode * Trace::createLookupNode(Node * sourceNode,VentureValuePtr sym)
{
  LookupNode * lookupNode = new LookupNode(sourceNode,sym);
  setValue(lookupNode,getValue(sourceNode));
  //cout << "createLookupNode(" << sourceNode << "," << lookupNode << ")";
  addChild(sourceNode,lookupNode);
  return lookupNode;
}


pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env,VentureValuePtr exp)
{
  RequestNode * requestNode = new RequestNode(operatorNode, operandNodes, env);
  OutputNode * outputNode = new OutputNode(operatorNode, operandNodes, requestNode, env, exp);

  //cout << "createApplicationNodes(" << operatorNode << "," << requestNode << ")";
  
  requestNode->outputNode = outputNode;
  addChild(requestNode, outputNode);
  
  addChild(operatorNode, requestNode);
  addChild(operatorNode, outputNode);
  
  for (size_t i = 0; i < operandNodes.size(); ++i) {
    addChild(operandNodes[i], requestNode);
    addChild(operandNodes[i], outputNode);
  }
  
  return make_pair(requestNode, outputNode);
}

/* Derived Getters */
shared_ptr<PSP> Trace::getPSP(ApplicationNode * node)
{
  return getMadeSP(getOperatorSPMakerNode(node))->getPSP(node);
}

VentureValuePtr Trace::getGroundValue(Node * node)
{
  VentureValuePtr value = getValue(node);
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  
  // TODO Hack!
  if (spRef) { return VentureValuePtr(new VentureSPRecord(getMadeSP(spRef->makerNode),getMadeSPAux(spRef->makerNode))); }
  else { return value; }
}

Node * Trace::getOperatorSPMakerNode(ApplicationNode * node)
{
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(getValue(node->operatorNode));
  assert(spRef);
  return spRef->makerNode;
}


vector<Node*> Trace::getParents(Node * node)
{
  vector<Node*> parents = node->getDefiniteParents();
  if (dynamic_cast<OutputNode*>(node)) 
  {
    vector<RootOfFamily> esrRoots = getESRParents(node);
    for (size_t i = 0; i < esrRoots.size(); ++i)
    {
      parents.push_back(esrRoots[i].get());
    }
  }
  return parents;
}

shared_ptr<Args> Trace::getArgs(ApplicationNode * node) { return shared_ptr<Args>(new Args(this,node)); }


///////// misc
OutputNode * Trace::getConstrainableNode(Node * node)
{
  Node * candidate = getOutermostNonReferenceNode(node);

  if (dynamic_cast<ConstantNode*>(candidate)) { throw "Cannot constrain a deterministic value."; }
  OutputNode * outputNode = dynamic_cast<OutputNode*>(candidate);
  assert(outputNode);

  if (!getMadeSP(getOperatorSPMakerNode(outputNode))->getPSP(outputNode)->isRandom())
  {
    throw "Cannot constrain a deterministic value.";
  }
  return outputNode;
}

Node * Trace::getOutermostNonReferenceNode(Node * node)
{
  if (dynamic_cast<ConstantNode*>(node)) { return node; }
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  if (lookupNode) { return getOutermostNonReferenceNode(lookupNode->sourceNode); }
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
  assert(outputNode);
  
  shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
  
  if (dynamic_pointer_cast<ESRRefOutputPSP>(psp))
  { 
    assert(getESRParents(outputNode).size() == 1);
    return getOutermostNonReferenceNode(getESRParents(outputNode)[0].get());
  }
  else if (dynamic_pointer_cast<ScopeIncludeOutputPSP>(psp))
  { 
    return getOutermostNonReferenceNode(outputNode->operandNodes[2]);
  }
  else
  {
    return node;
  }
}


double Trace::logDensityOfBlock(ScopeID scope) { return -1 * log(numBlocksInScope(scope)); }
