#include "flush.h"
#include "value.h"
#include "node.h"
#include "sp.h"
#include "omegadb.h"
#include "debug.h"

#include <iostream>


void flushDBComplete(OmegaDB * omegaDB)
{

    while (!omegaDB->flushQueue.empty())
    {
      FlushEntry f = omegaDB->flushQueue.front();
      if (f.flushAux) { f.owner->destroySPAux(f.spaux); }
      else if (f.spaux) { f.owner->flushFamily(f.spaux,f.id); }
      else 
      {
	f.owner->flushValue(f.value,f.nodeType); 
      }
      omegaDB->flushQueue.pop();
    }

    for (pair<pair<Node *,size_t>, Node*> p : omegaDB->spFamilyDBs)
    {
      destroyFamilyNodes(p.second);
    }
  
  delete omegaDB;
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


void flushDB(OmegaDB * omegaDB, bool isActive)
{
  for (pair<SP *,LatentDB *> p : omegaDB->latentDBs)
  { 
    p.first->destroyLatentDB(p.second);
  }
  // this could be in another thread
  if (!isActive) { flushDBComplete(omegaDB); }
  else { delete omegaDB; }
}
