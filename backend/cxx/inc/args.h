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

  vector<VentureValue *> makeVectorOfValues(const vector<Node*> & nodes)

  vector<VentureValue *> operands;
  VentureValue * request;
  vector<VentureValue *> esrs;
  SPAux * spaux;

};

#endif
