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
  if (frame.count(sym)) 
  { 
    return frame[sym]; 
  }
  else if (outerEnv.get() == NULL)
  { 
    throw "Cannot find symbol '" + sym + "'";
  }
  else 
  {
    return outerEnv->lookupSymbol(sym);
  }
}
 


