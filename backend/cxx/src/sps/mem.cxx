#include "value.h"
#include "node.h"
#include "exp.h"
#include "env.h"
#include "sp.h"


#include "sps/mem.h"

#include <boost/functional/hash.hpp>

VentureValue * MSPMakerSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  /* TODO GC share somewhere here? */
  return new VentureSP(node,new MSP(operands[0]));
}

size_t MSP::hashValues(vector<Node *> operands) const
{
  size_t seed = 0;
  for (Node * operand : operands) { seed += operand->getValue()->toHash(); }
  return seed;
}

VentureValue * MSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  uint32_t id = hashValues(operands);

  Environment env;
  env.addBinding("memoizedSP", sharedOperatorNode);
  vector<Expression> exps;
  exps.push_back(Expression("memoizedSP"));
  for (Node * operand : operands)
  {
    exps.push_back(Expression(operand->getValue()));
  }
  Expression exp(exps);
  return new VentureRequest({ESR(id,exp,env)});
}
