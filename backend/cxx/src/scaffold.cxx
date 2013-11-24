/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "node.h"
#include "scaffold.h"
#include "sp.h"
#include "lkernel.h"


#include <iostream>

void Scaffold::addResamplingNode(queue<pair<Node *, bool> > & q, Node * node)
{
  absorbing.erase(node);
  drg.emplace(node,false);
  for (Node * child : node->children) { q.emplace(child,false); }
}

Scaffold::Scaffold(set<Node *> principalNodes)
{
  /* TODO extended SCAFFOLD */
  assembleERG(principalNodes);
  disableBrush();
  setRegenCounts();

}

void Scaffold::assembleERG(set<Node *> principalNodes)
{
  queue<pair<Node *,bool> > q;
  for (Node * pNode : principalNodes) 
  { 
    /* This condition is overly cautious. We only need to include the 
       request node if the operator is AAA. */
    if (!pNode->sp()->isNullRequest() && pNode->nodeType == NodeType::OUTPUT)
    { q.emplace(pNode->requestNode,true); }

    q.emplace(pNode,true); 
  }

  while (!q.empty())
  {
    pair<Node *, bool> p = q.front();
    q.pop();

    Node * node = p.first;
    bool isPrincipal = p.second;
    assert(node->isValid());

    if (isResampling(node)) { continue; }
    // subtle, double check when under 100 degrees
//    else if (!node->isObservation() && node->isConstrained) { addResamplingNode(q,node); }
    else if (node->nodeType == NodeType::LOOKUP) { addResamplingNode(q,node); }
    else if (isResampling(node->operatorNode)) { addResamplingNode(q,node); }
    else if (!isPrincipal && node->sp()->canAbsorb(node->nodeType)) { addAbsorbingNode(node); }
    else if (node->sp()->childrenCanAAA) { addAAANode(node); }
    /* Special case for ESRReference */
    else if (esrReferenceCanAbsorb(node)) { addAbsorbingNode(node); }
    else { addResamplingNode(q,node); }
  }
}

bool Scaffold::hasChildInAorD(Node * node)
{
  /* TODO confirm that OR works with int return values. */
  for (Node * child : node->children)
  { if ((absorbing.count(child) > 0) || (drg.count(child) > 0)) { return true; } }
  return false;
}

void Scaffold::disableBrush() 
{
  map<Node *,uint32_t> disableCounts;
  for (pair<Node *,DRGNode> p : drg)
  {
    Node * node = p.first;
    if (node->nodeType == NodeType::REQUEST)
    { disableRequests(node,disableCounts); }
  }
}

void Scaffold::disableRequests(Node * node, 
			       map<Node *,uint32_t> & disableCounts)
{
  for (Node * esrParent : node->outputNode->esrParents)
  {
    if (disableCounts.count(esrParent)) { disableCounts[esrParent]++; }
    else { disableCounts[esrParent] = 1; }
    if (disableCounts[esrParent] == esrParent->numRequests)
    { disableEval(esrParent,disableCounts); }
  }
}

void Scaffold::disableEval(Node * node,     
			   map<Node *,uint32_t> & disableCounts)
{
  registerBrush(node);
  if (node->nodeType == NodeType::OUTPUT)
  {
    registerBrush(node->requestNode);
    disableRequests(node->requestNode,disableCounts);
    disableEval(node->operatorNode,disableCounts);
    for (Node * operandNode : node->operandNodes)
    { disableEval(operandNode,disableCounts); }
  }
}


void Scaffold::processParentAAA(Node * parent)
{
  if (parent->isReference())
  {
    if (!isResampling(parent) && isAAA(parent->sourceNode))
    { drg[parent->sourceNode].regenCount++; }
  }
  else
  {
    if (isAAA(parent))
    { drg[parent].regenCount++; }
  }
}

void Scaffold::processParentsAAA(Node * node)
{
  if (node->nodeType == NodeType::LOOKUP) { processParentAAA(node->lookedUpNode); }
  else
  {
    processParentAAA(node->operatorNode);
    for (Node * operandNode : node->operandNodes) { processParentAAA(operandNode); }
  
    if (node->nodeType == NodeType::OUTPUT)
    {
      processParentAAA(node->requestNode);
      for (Node * esrParent : node->esrParents) { processParentAAA(esrParent); }
    }
  }
}

void Scaffold::setRegenCounts()
{
  for (pair<Node *,DRGNode> p : drg)
  {
    Node * node = p.first;
    DRGNode &drgNode = drg[node];
    if (drgNode.isAAA)
    {
      drgNode.regenCount++;
      border.push_back(node);
      lkernels.insert({node,node->sp()->getAAAKernel()});
    }
    else if (!hasChildInAorD(node))
    {
      drgNode.regenCount = node->children.size() + 1;
      border.push_back(node);
    }
    else 
    { 
      drgNode.regenCount = node->children.size();
    }
  }

  // (costly) ~optimization, especially for particle methods
  set<Node *> nullAbsorbing;
  for (Node * node : absorbing)
  { 
    if (node->nodeType == NodeType::REQUEST &&
        !isResampling(node->operatorNode) &&
        node->sp()->isNullRequest())
    {
      for (Node * operandNode : node->operandNodes)
      {
        if (drg.count(operandNode) && !drg[operandNode].isAAA)
        {
          drg[operandNode].regenCount--;
          assert(drg[operandNode].regenCount > 0);
        }
      }
      nullAbsorbing.insert(node);
    }
  }
  for (Node * node : nullAbsorbing) { absorbing.erase(node); }

  /* TODO OPT fill the border with the absorbing nodes. Not sure if I need the absorbing
     nodes at all anymore, so may just rename absorbing to border and then push back
     the terminal nodes. */
  border.insert(border.end(),absorbing.begin(),absorbing.end());
  
  /* Now add increment the regenCount for AAA nodes as 
     is appropriate. */
  /* TODO Note that they may have been in the brush, in which case this is not necessary. */
  if (hasAAANodes)
  {
    for (pair<Node *,DRGNode> p : drg) { processParentsAAA(p.first); }
    for (Node * node : absorbing) { processParentsAAA(node); }
    for (Node * node : brush)
    {
      for (Node * esrParent : node->esrParents)
      { processParentAAA(esrParent); }
      if (node->nodeType == NodeType::LOOKUP)
      { processParentAAA(node->lookedUpNode); }
    }
  }
}

void Scaffold::loadDefaultKernels(bool deltaKernels) {}


bool Scaffold::esrReferenceCanAbsorb(Node * node)
{
  return 
    node->nodeType == NodeType::OUTPUT &&
    node->sp()->isESRReference &&
    !isResampling(node->requestNode) &&
    !isResampling(node->esrParents[0]);
}

void Scaffold::show()
{
  cout << "--Scaffold--" << endl;
  cout << "DRG" << endl;
  for (pair<Node*,DRGNode> p : drg)
  {
    assert(p.first->isValid());
    cout << p.first << " (" << p.second.regenCount << ", " << strNodeType(p.first->nodeType) <<", " << p.second.isAAA << ")" << endl;
  }

  cout << "Absorbing" << endl;
  for (Node * node : absorbing)
  {
    assert(node->isValid());
    cout << node <<  " (" << strNodeType(node->nodeType) << ")" << endl;
  }
  
  cout << "Border" << endl;
  for (Node * node : border)
  {
    cout << node << endl;
  }

  cout << "--End Scaffold--" << endl;
}

Scaffold::~Scaffold()
{
  for (pair<Node*,LKernel*> p : lkernels) { delete p.second; }
}

