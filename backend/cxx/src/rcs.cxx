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
#include "Python.h"
#include "trace.h"
#include <iostream>

void Trace::registerRandomChoice(Node * node)
{
//  cout << "REG: " << node << endl;
  assert(!rcToIndex.count(node));

  rcToIndex[node] = randomChoices.size();
  randomChoices.push_back(node);
}


void Trace::unregisterRandomChoice(Node * node)
{
//  cout << "UNREG: " << node << endl;
  assert(rcToIndex.count(node));

  uint32_t index = rcToIndex[node];
  uint32_t lastIndex = randomChoices.size()-1;

  Node * lastNode = randomChoices[lastIndex];
  rcToIndex[lastNode] = index;
  randomChoices[index] = lastNode;
  randomChoices.pop_back();
  rcToIndex.erase(node);
  assert(rcToIndex.size() == randomChoices.size());
}

void Trace::registerConstrainedChoice(Node * node)
{
//  cout << "REG-CON: " << node << endl;
  assert(!ccToIndex.count(node));

  ccToIndex[node] = constrainedChoices.size();
  constrainedChoices.push_back(node);
}


void Trace::unregisterConstrainedChoice(Node * node)
{
//  cout << "UNREG-CON: " << node << endl;
  assert(ccToIndex.count(node));

  uint32_t index = ccToIndex[node];
  uint32_t lastIndex = constrainedChoices.size()-1;

  Node * lastNode = constrainedChoices[lastIndex];
  ccToIndex[lastNode] = index;
  constrainedChoices[index] = lastNode;
  constrainedChoices.pop_back();
  ccToIndex.erase(node);
  assert(ccToIndex.size() == constrainedChoices.size());
}

vector<Node *> Trace::getRandomChoices() { return randomChoices; }

void Trace::registerAEKernel(VentureSP * vsp)
{
  cout << "Warning -- Trace::registerAEKernel not yet implemented." << endl;
  assert(false);
}

void Trace::unregisterAEKernel(VentureSP * vsp)
{
  cout << "Warning -- Trace::unregisterAEKernel yet implemented." << endl;
  assert(false);
}

