#include "flush.h"
#include "value.h"
#include "node.h"
#include "sp.h"
#include "omegadb.h"
#include "debug.h"

#include <iostream>

FlushType nodeTypeToFlushType(NodeType nodeType)
{
  switch (nodeType)
  {
  case NodeType::REQUEST: { return FlushType::REQUEST; }
  case NodeType::OUTPUT: { return FlushType::OUTPUT; }
  default: { assert(false); }
  }
}

void flushDB(OmegaDB * omegaDB, bool isActive)
{
  for (pair<SP *,LatentDB *> p : omegaDB->latentDBs)
  { 
    p.first->destroyLatentDB(p.second);
  }

  if (!isActive)
  { 

    while (!omegaDB->flushQueue.empty())
    {
      FlushEntry f = omegaDB->flushQueue.front();
      if (f.owner) { f.owner->flushValue(f.value,f.flushType); }
      else { delete f.value; }
      omegaDB->flushQueue.pop();
    }

    for (pair<pair<Node *,size_t>, Node*> p : omegaDB->spFamilyDBs)
    {
      destroyFamilyNodes(p.second);
    }
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

