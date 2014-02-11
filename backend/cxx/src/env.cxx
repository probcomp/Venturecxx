#include "env.h"

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

Node * VentureEnvironment::lookupSymbol(shared_ptr<VentureSymbol> sym) const
{
  return lookupSymbol(sym->s);
}

Node * VentureEnvironment::lookupSymbol(string sym) const
{
  if (frame.count(sym)) 
  { 
    return frame[sym]; 
  }
  else if (outerEnv.get() == NULL)
  { 
    cout << "Cannot find symbol: " << sym << endl;
    throw "Cannot find symbol: " + sym;
    return NULL;
  }
  else 
  {
    return outerEnv->lookupSymbol(sym);
  }
}
 


