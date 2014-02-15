#include "trace.h"
#include "sp.h"
#include "sprecord.h"
#include "args.h"

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
  //cout << "createLookupNode(" << sourceNode << "," << lookupNode << ")";
  addChild(sourceNode,lookupNode);
  return lookupNode;
}


pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node * operatorNode, const vector<Node*>& operandNodes, const shared_ptr<VentureEnvironment>& env)
{
  RequestNode * requestNode = new RequestNode(operatorNode, operandNodes, env);
  OutputNode * outputNode = new OutputNode(operatorNode, operandNodes, requestNode, env);

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

/* Derived getters */

VentureValuePtr Trace::getGroundValue(Node * node)
{
  VentureValuePtr value = getValue(node);
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  
  if (spRef) { return getValue(spRef->makerNode); }
  else { return value; }
}

Node * Trace::getOperatorSPMakerNode(ApplicationNode * node)
{
  shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(getValue(node->operatorNode));
  assert(spRef);
  return spRef->makerNode;
}

shared_ptr<VentureSP> Trace::getMadeSP(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->sp;
}

shared_ptr<SPFamilies> Trace::getMadeSPFamilies(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spFamilies;
}

shared_ptr<SPAux> Trace::getMadeSPAux(Node * makerNode)
{
  shared_ptr<VentureSPRecord> spRecord = getMadeSPRecord(makerNode);
  return spRecord->spAux;
}

vector<Node*> Trace::getParents(Node * node)
{
  vector<Node*> parents = node->definiteParents;
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
OutputNode * Trace::getOutermostNonRefAppNode(Node * node)
{
  LookupNode * lookupNode = dynamic_cast<LookupNode*>(node);
  if (lookupNode) { return getOutermostNonRefAppNode(lookupNode->sourceNode); }
  OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
  assert(outputNode);
  if (dynamic_pointer_cast<ESRRefOutputPSP>(getMadeSP(getOperatorSPMakerNode(outputNode))->getPSP(outputNode)))
  { 
    return getOutermostNonRefAppNode(getESRParents(outputNode)[0].get());
  }
  else { return outputNode; }
}
