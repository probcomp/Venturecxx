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
#include "node.h"
#include "env.h"
#include <iostream>
#include <cassert>

void VentureEnvironment::addBinding(VentureSymbol * vsym, Node * node) 
{ 
  frame.insert({vsym->sym,node}); 
  vsyms.push_back(vsym);
}

void VentureEnvironment::destroySymbols()
{
  for (VentureSymbol * vsym : vsyms) { delete vsym; }
}


Node * VentureEnvironment::findSymbol(VentureSymbol * vsym)
{
  return findSymbol(vsym->sym);
}

Node * VentureEnvironment::findSymbol(const string & sym)
{
  if (frame.count(sym)) 
  { 
    return frame[sym]; 
  }
  else if (outerEnv == nullptr) 
  { 
    cout << "Cannot find symbol: " << sym << endl;
    throw "Cannot find symbol: " + sym;
    return nullptr;
  }
  else 
  {
    return outerEnv->findSymbol(sym);
  }
}
