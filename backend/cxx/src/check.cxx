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
#include "check.h"
#include "node.h"
#include "trace.h"
#include "scaffold.h"
#include "node.h"

void TraceConsistencyChecker::checkConsistency()
{
//  uint32_t numUCRCs = 0;  // unconstrained random choices
//  uint32_t numCRCs = 0;   // constrained random choices

//  map<pair<Node *,size_t>, Node *> spFamilies;
  
//  map<size_t,pair<Node*,VentureValue*> > ventureFamilies;

  // Iterate over each Venture family, 
//  for (pair<size_t,pair<Node*,VentureValue*> > pp : ventureFamilies)
//  {
//    Node * root = pp.second.first;
    
    



//  }

  assert(false);
}



void TraceConsistencyChecker::checkTorus(Scaffold * scaffold)
{
  bool fail = false;
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    if (p.first->isActive) { fail = true; }
    if (p.second.regenCount != 0) { fail = true; }
  }
  assert(!fail);
}

void TraceConsistencyChecker::checkWhole(Scaffold * scaffold)
{
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    assert(p.first->isActive);
    assert(p.second.regenCount > 0);
  }
}

