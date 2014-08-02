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
  CSPRequestPSP(const vector<string>& symbols, VentureValuePtr expression, shared_ptr<VentureEnvironment> environment);

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return true; }
  CSPRequestPSP* copy_help(ForwardingMap* m) const;

private:
  vector<string> symbols;
  VentureValuePtr expression;
  shared_ptr<VentureEnvironment> environment;
};

#endif
