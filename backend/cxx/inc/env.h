#ifndef ENV_H
#define ENV_H

#include "value.h"
#include "all.h"
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

struct Node;

struct VentureEnvironment : VentureValue
{
  VentureEnvironment() {}
  VentureEnvironment(VentureEnvironment * outerEnv): outerEnv(outerEnv) {}

  void addBinding(VentureSymbol * vsym, Node * node);

  unordered_map<string, Node *> frame;
  vector<VentureSymbol*> vsyms;

  void destroySymbols();

  VentureEnvironment * outerEnv{nullptr};

  Node * findSymbol(VentureSymbol * vsym);

private:
  Node * findSymbol(const string & sym);
};


#endif
