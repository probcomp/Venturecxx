#include "psp.h"
#include "values.h"
#include "args.h"
#include "concrete_trace.h"
#include "node.h"

#include <iostream>

using std::cout;
using std::endl;

VentureValuePtr NullRequestPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  return shared_ptr<VentureRequest>(new VentureRequest(vector<ESR>(),vector<shared_ptr<LSR> >()));
}


VentureValuePtr ESRRefOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
//  cout << "ESRRefOutputPSP::simulate(" << args->node << ")" << endl;
  assert(args->esrParentNodes.size() == 1);
  return args->esrParentValues[0];
}

bool ESRRefOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  vector<RootOfFamily> esrParents = trace->getESRParents(appNode);
  assert(esrParents.size() == 1);
  if (parentNode == esrParents[0].get()) { return false; }
  OutputNode * outputNode = dynamic_cast<OutputNode*>(appNode);
  if (outputNode && parentNode == outputNode->requestNode) { return false; }
  return true;
}
