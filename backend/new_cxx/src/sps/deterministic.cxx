#include "sps/deterministic.h"
#include "utils.h"
#include <cmath>

#include <iostream>
using std::cout;
using std::endl;
VentureValuePtr AddOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  double sum = 0;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    sum += args->operandValues[i]->getDouble();
  }
  return shared_ptr<VentureNumber>(new VentureNumber(sum));
}

VentureValuePtr SubOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("minus", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() - args->operandValues[1]->getDouble()));
}

VentureValuePtr MulOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  double prod = 1;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    prod *= args->operandValues[i]->getDouble();
  }
  return shared_ptr<VentureNumber>(new VentureNumber(prod));
}


VentureValuePtr DivOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("divide", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() / args->operandValues[1]->getDouble()));
}

VentureValuePtr IntDivOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("integer divide", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getInt() / args->operandValues[1]->getInt()));
}

VentureValuePtr IntModOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("integer mod", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getInt() % args->operandValues[1]->getInt()));
}

VentureValuePtr EqOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("equals", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->equals(args->operandValues[1])));
}

VentureValuePtr GtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength(">", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() > args->operandValues[1]->getDouble()));
}

VentureValuePtr GteOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength(">=", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() >= args->operandValues[1]->getDouble()));
}

VentureValuePtr LtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("<", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() < args->operandValues[1]->getDouble()));
}

VentureValuePtr LteOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("<=", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() <= args->operandValues[1]->getDouble()));
}


VentureValuePtr SinOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("sin", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(sin(args->operandValues[0]->getDouble())));
}


VentureValuePtr CosOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("cos", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(cos(args->operandValues[0]->getDouble())));
}


VentureValuePtr TanOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("tan", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(tan(args->operandValues[0]->getDouble())));
}


VentureValuePtr HypotOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("hypot", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(hypot(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble())));
}

VentureValuePtr ExpOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("exp", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(exp(args->operandValues[0]->getDouble())));
}

VentureValuePtr LogOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("log", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(log(args->operandValues[0]->getDouble())));
}

VentureValuePtr PowOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("pow", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(pow(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble())));
}

VentureValuePtr SqrtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("sqrt", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(sqrt(args->operandValues[0]->getDouble())));
}

VentureValuePtr NotOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("not", args, 1);
  return shared_ptr<VentureBool>(new VentureBool(!args->operandValues[0]->getBool()));
}

VentureValuePtr IsSymbolOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("is_symbol", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureSymbol>(args->operandValues[0]) != NULL));
}

VentureValuePtr ToAtomOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("to_atom", args, 1);
  return VentureValuePtr(new VentureAtom(args->operandValues[0]->getInt()));
}

VentureValuePtr IsAtomOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("is_atom", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureAtom>(args->operandValues[0]) != NULL));
}

VentureValuePtr ProbabilityOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("probability", args, 1);
  return VentureValuePtr(new VentureProbability(args->operandValues[0]->getProbability()));
}
