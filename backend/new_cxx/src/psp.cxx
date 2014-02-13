#include "psp.h"
#include "values.h"

VentureValuePtr NullRequestPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  return shared_ptr<VentureRequest>(new VentureRequest(vector<ESR>(),vector<shared_ptr<LSR> >()));
}


VentureValuePtr ESRRefOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  throw 500;
}

bool ESRRefOutputPSP::canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const
{
  throw 500;
}
