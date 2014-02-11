#include "trace.h"
#include "node.h"
#include "spaux.h"
#include "srs.h"
#include "value.h"

// Mutates the set
void findSPFamilyRootsHelper(set<Node *> & roots, Node * node);

set<Node *> Trace::findSPFamilyRoots()
{
  set<Node *> roots{};

  for (pair<size_t,pair<Node *,VentureValue*> > pp : ventureFamilies)
  {
    Node * vroot = pp.second.first;
    findSPFamilyRootsHelper(roots,vroot);
  }
  
  return roots;
}


void findSPFamilyRootsHelper(set<Node *> & roots, Node * node)
{
  if (node->nodeType == NodeType::VALUE) { return; }
  if (node->nodeType == NodeType::LOOKUP) { return; }
  assert(node->nodeType == NodeType::OUTPUT);

  VentureRequest * requests = dynamic_cast<VentureRequest *>(node->requestNode->getValue());
  if (requests)
  {
    for (ESR esr : requests->esrs)
    {
      assert(node->spaux()->families.count(esr.id));
      Node * sproot = node->spaux()->families[esr.id];
      if (!roots.count(sproot))
      {
	roots.insert(sproot);
	findSPFamilyRootsHelper(roots,sproot);
      }
    }
  }
  
  findSPFamilyRootsHelper(roots,node->operatorNode);
  for (Node * operandNode : node->operandNodes)
  {
    findSPFamilyRootsHelper(roots,operandNode);
  }
  
}
