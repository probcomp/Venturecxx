#ifndef ARGS_H
#define ARGS_H

struct Args
{
  Args(Trace * trace, Node * node);

  Node * node;
  vector<VentureValuePtr> operandValues;
  vector<Node*> operandNodes;

  shared_ptr<VentureRequest> requestValue;
  Node * requestNode;

  vector<VentureValuePtr> esrParentValues;
  vector<Node*> esrParentNodes;

  shared_ptr<SPAux> spAux;
  shared_ptr<SPAux> madeSPAux;

  shared_ptr<VentureEnvironment> env;

};



#endif
