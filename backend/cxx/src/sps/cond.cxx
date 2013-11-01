#include "node.h"
#include "spaux.h"
#include "value.h"


#include "sps/cond.h"


#include <cassert>
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>


VentureValue * BranchSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(node);
  Environment env;

  vector<Node *> & operands = node->operandNodes;
  VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
  assert(b);

  size_t index = 2;
  if (b->pred) { index = 1; }
  env.addBinding("f",operands[index]);
  vector<Expression> exps{Expression("f")};
  Expression exp(exps);
  return new VentureRequest({ESR(id,exp,env)});
}

