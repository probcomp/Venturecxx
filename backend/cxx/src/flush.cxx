#include "flush.h"
#include "value.h"
#include "node.h"
#include "sp.h"
#include "omegadb.h"
#include "debug.h"

void flushDB(OmegaDB & omegaDB)
{
  for (pair<Node *,LatentDB *> p : omegaDB.latentDBs)
  { 
    VentureSP * vsp = dynamic_cast<VentureSP *>(p.first->getValue());
    vsp->sp->destroyLatentDB(p.second);
  }

  while (!omegaDB.flushQueue.empty())
  {
    FlushEntry f = omegaDB.flushQueue.front();
    if (f.owner) { f.owner->flushValue(f.value,f.nodeType); }
    else { delete f.value; }
    omegaDB.flushQueue.pop();
  }

//  map<pair<Node *,size_t>, Node *> spFamilyDBs;

  for (pair<pair<Node *,size_t>, Node*> p : omegaDB.spFamilyDBs)
  {
    Node * root = p.second;
    delete root->familyEnvNode;
    destroyFamilyNodes(root);
  }
}


void destroyFamilyNodes(Node * node)
{
  if (node->nodeType == NodeType::VALUE || node->nodeType == NodeType::LOOKUP)
  { delete node; }
  else
  {
    destroyFamilyNodes(node->operatorNode);
    for (Node * operandNode : node->operandNodes)
    { destroyFamilyNodes(operandNode); }
    delete node->requestNode;
    delete node;
  }
}

