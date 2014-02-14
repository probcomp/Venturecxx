#include "sps/msp.h"
#include "sp.h"
#include "env.h"

VentureValuePtr MakeMSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  assert(args->operandValues.size() == 1); // TODO throw an error once exceptions work
  
  VentureValuePtr sharedSP = args->operandValues[0];
  
  assert(dynamic_pointer_cast<VentureSP>(sharedSP)); // TODO throw an error once exceptions work
  
  return VentureValuePtr(new VentureSP(new MSPRequestPSP(sharedSP), new ESRRefOutputPSP()));
}

MSPRequestPSP::MSPRequestPSP(VentureValuePtr sharedSP) : sharedSP(sharedSP) {}

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
  exp.push_back(sharedSP);
  
  size_t hash = 0;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    VentureValuePtr& operandValue = args->operandValues[i];
    exp.push_back(quote(operandValue));
    boost::hash_combine(hash, operandValue->hash());
  }
  
  shared_ptr<VentureEnvironment> empty(new VentureEnvironment());
  
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureAtom(hash)),VentureValuePtr(new VentureArray(exp)),empty));
  
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
