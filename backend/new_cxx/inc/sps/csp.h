#ifndef CSP_H
#define CSP_H

#include "psp.h"
#include "args.h"

struct MakeCSPOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct CSPRequestPSP : PSP
{
  CSPRequestPSP(shared_ptr<VentureArray> symbols, VentureValuePtr expression, shared_ptr<VentureEnvironment> environment);

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,Node * appNode,Node * parentNode) const { return true; }

private:
  shared_ptr<VentureArray> symbols;
  VentureValuePtr expression;
  shared_ptr<VentureEnvironment> environment;
};

#endif
