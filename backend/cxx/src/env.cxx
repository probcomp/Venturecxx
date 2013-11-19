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
    assert(frame[sym]);
    assert(frame[sym]->isValid());
    return frame[sym]; 
  }
  else if (outerEnv == nullptr)
  { 
    cout << "Cannot find symbol: " << sym << endl;
    assert(outerEnv);
    return nullptr;
  }
  else 
  {
    return outerEnv->findSymbol(sym);
  }
}
