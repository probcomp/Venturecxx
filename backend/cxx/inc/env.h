#ifndef ENV_H
#define ENV_H

#include <string>
#include <unordered_map>

using namespace std;

struct Node;

struct Environment
{
  Environment() {}
  Environment(Node * outerEnvNode): outerEnvNode(outerEnvNode) {}

  void addBinding(string s, Node * node) { frame.insert({s,node}); }

  unordered_map<string, Node *> frame;
  Node * outerEnvNode{nullptr};

  Node * findSymbol(const string & sym);
};

#endif
