#include "sps/msp.h"
#include "sprecord.h"
#include "env.h"

VentureValuePtr MakeMSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 1); // TODO throw an error once exceptions work
  return VentureValuePtr(new VentureSPRecord(new SP(new MSPRequestPSP(args->operandNodes[0]), new ESRRefOutputPSP())));
}

MSPRequestPSP::MSPRequestPSP(Node * sharedOperatorNode) : sharedOperatorNode(sharedOperatorNode) {}

VentureValuePtr quote(const VentureValuePtr& v)
{
  vector<VentureValuePtr> exp;
  exp.push_back(VentureValuePtr(new VentureSymbol("quote")));
  exp.push_back(v);
  return VentureValuePtr(new VentureArray(exp));
}

VentureValuePtr MSPRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> exp;
  exp.push_back(shared_ptr<VentureSymbol>(new VentureSymbol("memoizedSP")));
  
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    exp.push_back(quote(args->operandValues[i]));
  }
  
  shared_ptr<VentureEnvironment> empty(new VentureEnvironment());
  empty->addBinding(shared_ptr<VentureSymbol>(new VentureSymbol("memoizedSP")),sharedOperatorNode);
  
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureArray(args->operandValues)),VentureValuePtr(new VentureArray(exp)),empty));
  
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
