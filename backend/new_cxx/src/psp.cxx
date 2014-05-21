#include "psp.h"
#include "values.h"
#include "args.h"
#include "concrete_trace.h"
#include "node.h"
#include "lkernel.h"

#include <iostream>
#include <boost/foreach.hpp>

using std::cout;
using std::endl;

shared_ptr<LKernel> const PSP::getAAALKernel() { return shared_ptr<LKernel>(new DefaultAAALKernel(this)); }

pair<VentureValuePtr, vector<VentureValuePtr> > PSP::gradientOfLogDensity(const VentureValuePtr x, const shared_ptr<Args> args) {
  throw "error: the log of density function of "+this->toString()+" is not implemented.";
}

vector<VentureValuePtr> PSP::gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const {
  throw "error: the gradient of simulate of "+this->toString()+" is not implemented.";
}


VentureValuePtr NullRequestPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  return shared_ptr<VentureRequest>(new VentureRequest(vector<ESR>(),vector<shared_ptr<LSR> >()));
}

vector<VentureValuePtr> NullRequestPSP::gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const {
  vector<VentureValuePtr> grad;
  BOOST_FOREACH(VentureValuePtr value, args->operandValues) {
    grad.push_back(VentureNumber::makeValue(0));
  }
  return grad;
}

pair<VentureValuePtr, vector<VentureValuePtr> > NullRequestPSP::gradientOfLogDensity(const VentureValuePtr x, const shared_ptr<Args> args) {
  vector<VentureValuePtr> grad;
  BOOST_FOREACH(VentureValuePtr arg,  args->operandValues) {
    grad.push_back(VentureNumber::makeValue(0));
  }
  return make_pair(VentureNumber::makeValue(0), grad); 
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

vector<VentureValuePtr> ESRRefOutputPSP::gradientOfSimulate(const shared_ptr<Args> args, const VentureValuePtr value, const VentureValuePtr direction) const {
  vector<VentureValuePtr> grad;
  BOOST_FOREACH(VentureValuePtr value, args->operandValues) {
    grad.push_back(VentureNumber::makeValue(0));
  }
  vector<VentureValuePtr> directions = direction->getArray();
  grad.insert(grad.end(), directions.begin(), directions.end());
  return grad;
}

pair<VentureValuePtr, vector<VentureValuePtr> > ESRRefOutputPSP::gradientOfLogDensity(const VentureValuePtr x, const shared_ptr<Args> args) {
  vector<VentureValuePtr> grad;
  BOOST_FOREACH(VentureValuePtr arg,  args->operandValues) {
    grad.push_back(VentureNumber::makeValue(0));
  }
  return make_pair(VentureNumber::makeValue(0), grad); 
}