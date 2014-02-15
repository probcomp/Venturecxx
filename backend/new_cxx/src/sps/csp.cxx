#include "sps/csp.h"
#include "sp.h"
#include "env.h"

VentureValuePtr MakeCSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 2); // TODO throw an error once exceptions work

  shared_ptr<VentureArray> symbols = dynamic_pointer_cast<VentureArray>(args->operandValues[0]);
  assert(symbols); // TODO throw an error once exceptions work
  
  VentureValuePtr expression = args->operandValues[1];
  
  return VentureValuePtr(new VentureSPRecord(new SP(new CSPRequestPSP(symbols, expression, args->env), new ESRRefOutputPSP())));
}

CSPRequestPSP::CSPRequestPSP(shared_ptr<VentureArray> symbols, VentureValuePtr expression, shared_ptr<VentureEnvironment> environment) :
  symbols(symbols),
  expression(expression),
  environment(environment)
{}

VentureValuePtr CSPRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandNodes.size() == symbols->xs.size()); // TODO throw an error once exceptions work
  
  shared_ptr<VentureEnvironment> extendedEnv = shared_ptr<VentureEnvironment>(new VentureEnvironment(environment));
  
  for (size_t i = 0; i < symbols->xs.size(); ++i)
  {
    shared_ptr<VentureSymbol> symbol = dynamic_pointer_cast<VentureSymbol>(symbols->xs[i]);
    assert(symbol); // TODO throw an error once exceptions work
    extendedEnv->addBinding(symbol, args->operandNodes[i]);
  }
  
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),expression,extendedEnv));
  
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
