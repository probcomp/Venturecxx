#include "scaffold.h"

#include <iostream>

void Scaffold::addResamplingNode(std::queue<std::pair<Node *, bool> > & q, Node * node)
{
  absorbing.erase(node);
  drg.emplace(node,false);
  for (Node * child : node->children) { q.emplace(child,false); }
}

Scaffold::Scaffold(std::set<Node *> principalNodes)
{
  assembleERG(principalNodes);
  disableBrush();
  setRegenCounts();
}


void Scaffold::assembleERG(std::set<Node *> principalNodes)
{
  std::queue<std::pair<Node *,bool> > q;
  for (Node * pNode : principalNodes) { q.emplace(pNode,true); }

  while (!q.empty())
  {
    std::pair<Node *, bool> p = q.front();
    q.pop();

    Node * node = p.first;
    bool isPrincipal = p.second;

    if (isResampling(node)) { continue; }
    else if (node->isConstrained) { addResamplingNode(q,node); }
    else if (node->nodeType == NodeType::LOOKUP) { addResamplingNode(q,node); }
    else if (isResampling(node->operatorNode)) { addResamplingNode(q,node); }
    else if (!isPrincipal && node->sp->canAbsorb(node->nodeType)) { addAbsorbingNode(node); }
    /* Special case for CSRReference */
    else if (csrReferenceCanAbsorb(node)) { addAbsorbingNode(node); }
    else if (node->sp->childrenCanAAA) { addAAANode(node); }
    else { addResamplingNode(q,node); }
  }
}

bool Scaffold::hasChildInAorD(Node * node)
{
  /* TODO confirm that OR works with int return values. */
  for (Node * child : node->children)
  { if (absorbing.count(child) || drg.count(child)) { return true; } }
  return false;
}

void Scaffold::disableBrush() 
{
  std::unordered_map<Node *,uint32_t> disableCounts;
  for (std::pair<Node *,DRGNode> p : drg)
  {
    Node * node = p.first;
    if (node->nodeType == NodeType::REQUEST)
    { disableRequests(node,disableCounts); }
  }
}

void Scaffold::disableRequests(Node * node, 
			       std::unordered_map<Node *,uint32_t> & disableCounts)
{
  for (Node * csrParent : node->outputNode->csrParents)
  {
    if (disableCounts.count(csrParent)) { disableCounts[csrParent]++; }
    else { disableCounts[csrParent] = 1; }
    if (disableCounts[csrParent] == csrParent->numRequests)
    { disableEval(csrParent,disableCounts); }
  }
}

void Scaffold::disableEval(Node * node,     
			   std::unordered_map<Node *,uint32_t> & disableCounts)
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
  if (!isResampling(parent) && isAAA(parent->sourceNode))
  { drg[parent->sourceNode].regenCount++; }
}

void Scaffold::processParentsAAA(Node * node)
{
  for (Node * parent : node->parents) { processParentAAA(parent); }
}

/* Note new feature: we only count a (->Request, ->Output) pair as one. */
void Scaffold::setRegenCounts()
{
  for (std::pair<Node *,DRGNode> p : drg)
  {
    Node * node = p.first;
    /* TODO is this necessary? It didn't seem to be a reference otherwise. */
    DRGNode &drgNode = drg[node];
    if (drgNode.isAAA)
    {
      drgNode.regenCount++;
      border.push_back(node);
    }
    else if (!hasChildInAorD(node))
    {
      drgNode.regenCount = node->children.size() + 1;
      border.push_back(node);
    }
    else { 
      drgNode.regenCount = node->children.size();
    }
  }

  /* TODO OPT fill the border with the absorbing nodes. Not sure if I need the absorbing
     nodes at all anymore, so may just rename absorbing to border and then push back
     the terminal nodes. */
  border.insert(border.end(),absorbing.begin(),absorbing.end());

  /* Now add increment the regenCount for AAA nodes as 
     is appropriate. */
  if (hasAAANodes)
  {
    for (std::pair<Node *,DRGNode> p : drg) { processParentsAAA(p.first); }
    for (Node * node : absorbing) { processParentsAAA(node); }
    for (Node * node : brush)
    {
      for (Node * csrParent : node->csrParents)
      { processParentAAA(csrParent); }
      if (node->nodeType == NodeType::LOOKUP)
      { processParentAAA(node->lookedUpNode); }
    }
  }
}

void Scaffold::loadDefaultKernels(bool deltaKernels) {}




std::ostream& operator<<(std::ostream& os, Scaffold * scaffold) {
  os << "---Scaffold---" << std::endl;
  for (std::pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    os << p.first->address.toString() << std::endl;
  }
  os << "---end---" << std::endl;
  return os;
}

