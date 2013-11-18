#ifndef ARGS_H
#define ARGS_H

#include "all.h"
#include <vector>

struct Node;
struct VentureValue;
struct SPAux;
struct VentureEnvironment;


struct Args
{
  Args(Node * node);

  vector<VentureValue *> makeVectorOfValues(const vector<Node*> & nodes);

  vector<VentureValue *> operands;
  vector<Node *> operandNodes;

  VentureValue * request{nullptr};
  Node * requestNode{nullptr};

  vector<VentureValue *> esrs;
  vector<Node *> esrNodes;

  SPAux * spaux{nullptr};
  SPAux * madeSPAux{nullptr};

  VentureEnvironment * familyEnv{nullptr};

};

#endif
