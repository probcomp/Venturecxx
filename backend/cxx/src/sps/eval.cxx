#include "sps/eval.h"
#include "env.h"
#include "value.h"
#include "node.h"
#include "srs.h"
#include "all.h"
#include <vector>

VentureValue * EvalSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(node);


  vector<Node *> & operands = node->operandNodes;
  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(operands[1]->getValue());
  assert(env);
  return new VentureRequest({ESR(id,operands[0]->getValue(),env)});
}
