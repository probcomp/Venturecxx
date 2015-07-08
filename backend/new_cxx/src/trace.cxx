// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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


pair<RequestNode*,OutputNode*> Trace::createApplicationNodes(Node * operatorNode, const vector<Node*>& operandNodes, const boost::shared_ptr<VentureEnvironment>& env,VentureValuePtr exp)
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
boost::shared_ptr<PSP> Trace::getPSP(ApplicationNode * node)
{
  return getMadeSP(getOperatorSPMakerNode(node))->getPSP(node);
}

VentureValuePtr Trace::getGroundValue(Node * node)
{
  VentureValuePtr value = getValue(node);
  boost::shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(value);
  
  // TODO Hack!
  if (spRef) { return VentureValuePtr(new VentureSPRecord(getMadeSP(spRef->makerNode),getMadeSPAux(spRef->makerNode))); }
  else { return value; }
}

Node * Trace::getOperatorSPMakerNode(ApplicationNode * node)
{
  VentureValuePtr candidate = getValue(node->operatorNode);
  boost::shared_ptr<VentureSPRef> spRef = dynamic_pointer_cast<VentureSPRef>(candidate);
  if (!spRef)
  {
    throw "Cannot apply a non-procedure: " + candidate->toString();
  }
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

boost::shared_ptr<Args> Trace::getArgs(ApplicationNode * node) { return boost::shared_ptr<Args>(new Args(this,node)); }


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
  
  boost::shared_ptr<PSP> psp = getMadeSP(getOperatorSPMakerNode(outputNode))->getPSP(outputNode);
  
  if (dynamic_pointer_cast<ESRRefOutputPSP>(psp))
  { 
    assert(getESRParents(outputNode).size() == 1);
    return getOutermostNonReferenceNode(getESRParents(outputNode)[0].get());
  }
  else if (dynamic_pointer_cast<TagOutputPSP>(psp))
  { 
    return getOutermostNonReferenceNode(outputNode->operandNodes[2]);
  }
  else
  {
    return node;
  }
}


double Trace::logDensityOfBlock(ScopeID scope) { return -1 * log(numBlocksInScope(scope)); }
