#include "psp.h"
#include "values.h"
#include "args.h"
#include "concrete_trace.h"
#include "node.h"
#include "lkernel.h"

#include <iostream>

using std::cout;
using std::endl;

shared_ptr<LKernel> const PSP::getAAALKernel() { return shared_ptr<LKernel>(new DefaultAAALKernel(this)); }

pair<VentureValuePtr, vector<VentureValuePtr>> PSP::gradientOfLogDensity(const VentureValuePtr x, const shared_ptr<Args> args)  const{
	vector<VentureValuePtr> grad;
	for(VentureValuePtr arg : args->operandValues) {
		grad.push_back(VentureNumber::makeValue(0));
	}
	return make_pair(VentureNumber::makeValue(0), grad); 
}

vector<VentureValuePtr> PSP::gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const {
  vector<VentureValuePtr> grad;
  for(auto value : args->operandValues) {
    grad.push_back(VentureNumber::makeValue(0));
  }
  vector<VentureValuePtr> directions = direction->getArray();
  grad.insert(grad.end(), directions.begin(), directions.end());
  return grad;
}


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

