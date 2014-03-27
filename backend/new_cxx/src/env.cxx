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

void VentureEnvironment::addBinding(shared_ptr<VentureSymbol> sym,Node * node)
{
  assert(!frame.count(sym->s));
  frame[sym->s] = node; 
}

Node * VentureEnvironment::lookupSymbol(shared_ptr<VentureSymbol> sym)
{
  return lookupSymbol(sym->s);
}

Node * VentureEnvironment::lookupSymbol(const string& sym) 
{
  if (frame.count(sym)) 
  { 
    return frame[sym]; 
  }
  else if (outerEnv.get() == NULL)
  { 
    throw "Cannot find symbol: " + sym;
  }
  else 
  {
    return outerEnv->lookupSymbol(sym);
  }
}
 


