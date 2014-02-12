#ifndef ARGS_H
#define ARGS_H

#include "types.h"
#include "values.h"

struct Trace;
struct Node;
struct ApplicationNode;
struct RequestNode;
struct VentureRequest;
struct SPAux;
struct VentureEnvironment;

struct Args
{
  Args(Trace * trace, Node * node);

  ApplicationNode * node;
  vector<VentureValuePtr> operandValues;
  vector<Node*> operandNodes;

  shared_ptr<VentureRequest> requestValue;
  RequestNode * requestNode;

  vector<VentureValuePtr> esrParentValues;
  vector<Node*> esrParentNodes;

  shared_ptr<SPAux> spAux;
  shared_ptr<SPAux> madeSPAux;

  shared_ptr<VentureEnvironment> env;

};

#endif
