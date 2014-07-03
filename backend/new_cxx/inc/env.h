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

  int getValueTypeRank() const;

  void addBinding(const string& sym,Node * node);
  void removeBinding(const string& sym);
  Node * lookupSymbol(shared_ptr<VentureSymbol> sym);
  Node * lookupSymbol(const string& sym);

  shared_ptr<VentureEnvironment> outerEnv;
  map<string,Node*> frame;

  VentureEnvironment* copy_help(ForwardingMap* m) const;
};

#endif
