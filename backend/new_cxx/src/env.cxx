// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "env.h"

#include <iostream>

using std::cout;
using std::endl;

VentureEnvironment::VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv) : outerEnv(outerEnv) {}

VentureEnvironment::VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv,
				       const vector<shared_ptr<VentureSymbol> > & syms,
				       const vector<Node*> & nodes):
  outerEnv(outerEnv)
{
  assert(syms.size() == nodes.size());
  for (size_t i = 0; i < syms.size(); ++i)
  {
    frame[syms[i]->s] = nodes[i];
  }
}

void VentureEnvironment::addBinding(const string& sym, Node * node)
{
  if (frame.count(sym))
  {
    throw sym + " already defined.";
  }

  frame[sym] = node;
}

void VentureEnvironment::removeBinding(const string& sym)
{
  if (frame.count(sym))
  {
    frame.erase(sym);
  } else if (outerEnv.get() == NULL)
  {
    throw "Cannot unbind unbound symbol '" + sym + "'";
  }
  else
  {
    return outerEnv->removeBinding(sym);
  }
}

Node * VentureEnvironment::lookupSymbol(shared_ptr<VentureSymbol> sym)
{
  return lookupSymbol(sym->s);
}

Node * VentureEnvironment::lookupSymbol(const string& sym)
{
  Node* answer = safeLookupSymbol(sym);
  if (answer == NULL)
  {
    throw "Cannot find symbol '" + sym + "'";
  }
  else
  {
    return answer;
  }
}

Node * VentureEnvironment::safeLookupSymbol(const string& sym)
{
  if (frame.count(sym))
  {
    return frame[sym];
  }
  else if (outerEnv.get() == NULL)
  {
    return NULL;
  }
  else
  {
    return outerEnv->safeLookupSymbol(sym);
  }
}

