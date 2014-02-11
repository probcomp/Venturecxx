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

