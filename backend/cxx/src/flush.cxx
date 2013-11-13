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
    if (f.spaux) 
    { 
      assert(f.owner);
      assert(f.owner->isValid());
      assert(f.spaux->isValid());
      f.owner->destroySPAux(f.spaux);
    }
    else if (f.owner) 
    { 
      // value may not be valid here, but then the owner must know not to flush it
      f.owner->flushValue(f.value,f.nodeType); 
    }
    else 
    { 
      assert(f.value->isValid());
      deepDelete(f.value);
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

