#include "flush.h"
#include "value.h"
#include "node.h"
#include "sp.h"
#include "spaux.h"
#include "omegadb.h"
#include "debug.h"

#include <iostream>


void flushDBComplete(OmegaDB * omegaDB)
{
  while (!omegaDB->flushQueue.empty())
  {
    FlushEntry f = omegaDB->flushQueue.front();
    assert(f.owner);
    // value may not be valid here, but then the owner must know not to flush it
    f.owner->flushValue(f.value,f.nodeType); 
    omegaDB->flushQueue.pop();
  }

  // Don't stick it on flush queue directly because we need to have it to repopulate the spaux with
  // anyway (in the current hacked design). TODO have the ESR include the vector directly.
  for (pair<pair<Node *,size_t>, vector<VentureValue*> > pp : omegaDB->spOwnedValues)
  {
    for (VentureValue * v : pp.second)
    { deepDelete(v); }
  }

  for (pair<pair<Node *,size_t>, Node*> p : omegaDB->spFamilyDBs)
  {
    destroyFamilyNodes(p.second);
  }
  
  delete omegaDB;
}


void destroyFamilyNodes(Node * node)
{
  assert(node->isValid());
  if (node->nodeType == NodeType::VALUE || node->nodeType == NodeType::LOOKUP)
  { delete node; }
  else
  {
    destroyFamilyNodes(node->operatorNode);
    for (Node * operandNode : node->operandNodes)
    { destroyFamilyNodes(operandNode); }
    assert(node->requestNode->isValid());
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

