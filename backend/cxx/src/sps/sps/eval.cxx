#include "sps/eval.h"
#include "env.h"
#include "value.h"

#include "srs.h"
#include "all.h"
#include <vector>

VentureValue * EvalSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(args.outputNode);


  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(args.operands[1]);
  assert(env);
  return new VentureRequest({ESR(id,args.operands[0],env)});
}
