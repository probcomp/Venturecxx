#ifndef ENVIRONMENT_H
#define ENVIRONMENT_H

#include "types.h"
#include "value.h"
#include "values.h"
#include "node.h"

struct VentureEnvironment : VentureValue
{
  VentureEnvironment() {}

  VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv);

  VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv,
		     const vector<shared_ptr<VentureSymbol> > & syms,
		     const vector<Node*> & nodes);

  void addBinding(const string& sym,Node * node);
  Node * lookupSymbol(shared_ptr<VentureSymbol> sym);
  Node * lookupSymbol(const string& sym);

  shared_ptr<VentureEnvironment> outerEnv;
  map<string,Node*> frame;
};

#endif
