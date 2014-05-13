#include "gkernel.h"
#include "detach.h"
#include "utils.h"
#include "particle.h"
#include "consistency.h"
#include "regen.h"
#include "db.h"
#include "trace.h"
#include "args.h"
#include "lkernel.h"
#include <math.h>
#include <boost/foreach.hpp>

void registerDeterministicLKernels(Trace * trace,
  shared_ptr<Scaffold> scaffold,
  const vector<ApplicationNode*>& applicationNodes,
  const vector<VentureValuePtr>& values)
{
  for (size_t i = 0; i < applicationNodes.size(); ++i)
  {
    trace->registerLKernel(scaffold,applicationNodes[i],shared_ptr<DeterministicLKernel>(new DeterministicLKernel(values[i], trace->getPSP(applicationNodes[i]))));
  }
}

