#ifndef ARGS_H
#define ARGS_H

#include "all.h"
#include <vector>

struct Node;
struct VentureValue;
struct SPAux;
struct Trace;
struct VentureEnvironment;
enum class NodeType;

struct Args
{
  Args(Trace * trace, Node * node);
  
  vector<VentureValue *> makeVectorOfValues(const vector<Node*> & nodes);

  vector<VentureValue *> operands;
  vector<Node *> operandNodes;

  Node * requestNode{nullptr};
  Node * outputNode{nullptr};

  VentureValue * request{nullptr};

  vector<VentureValue *> esrs;
  vector<Node *> esrNodes;

  SPAux * spaux{nullptr};
  SPAux * madeSPAux{nullptr};

  VentureEnvironment * familyEnv{nullptr};

  bool isRequest{false};

};

#endif
