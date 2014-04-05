#include "sps/csp.h"
#include "sprecord.h"
#include "env.h"
#include "utils.h"

#include <boost/foreach.hpp>

VentureValuePtr MakeCSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("lambda", args, 2);
  
  vector<string> symbols;
  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray())
  {
    symbols.push_back(v->getSymbol());
  }
  
  VentureValuePtr expression = args->operandValues[1];
  
  return VentureValuePtr(new VentureSPRecord(new SP(new CSPRequestPSP(symbols, expression, args->env), new ESRRefOutputPSP())));
}

CSPRequestPSP::CSPRequestPSP(const vector<string>& symbols, VentureValuePtr expression, shared_ptr<VentureEnvironment> environment) :
  symbols(symbols),
  expression(expression),
  environment(environment)
{}

VentureValuePtr CSPRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("compound procedure", args, symbols.size());
  
  shared_ptr<VentureEnvironment> extendedEnv = shared_ptr<VentureEnvironment>(new VentureEnvironment(environment));
  
  for (size_t i = 0; i < symbols.size(); ++i)
  {
    extendedEnv->addBinding(symbols[i], args->operandNodes[i]);
  }
  
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),expression,extendedEnv));
  
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
