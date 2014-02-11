#include "sps/deterministic.h"
#include <cmath>

VentureValuePtr PlusOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  double sum = 0;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    sum += args->operandValues[i]->getDouble();
  }
  return new VentureNumber(sum);
}

VentureValuePtr MinusOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(args->operandValues[0]->getDouble() - args->operandValues[1]->getDouble());
}

VentureValuePtr TimesOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  double prod = 1;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    prod *= args->operandValues[i]->getDouble();
  }
  return new VentureNumber(prod);
}


VentureValuePtr DivOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(args->operandValues[0]->getDouble() / args->operandValues[1]->getDouble());
}

VentureValuePtr EqOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(args->operandValues[0]->equals(args->operandValues[1]));
}

VentureValuePtr GtOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(args->operandValues[0]->getDouble() > args->operandValues[1]->getDouble());
}

VentureValuePtr GteOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(args->operandValues[0]->getDouble() >= args->operandValues[1]->getDouble());
}

VentureValuePtr LtOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(args->operandValues[0]->getDouble() < args->operandValues[1]->getDouble());
}


VentureValuePtr LteOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(args->operandValues[0]->getDouble() <= args->operandValues[1]->getDouble());
}


VentureValuePtr SinOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(sin(args->operandValues[0]->getDouble()));
}


VentureValuePtr CosOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(cos(args->operandValues[0]->getDouble()));
}


VentureValuePtr TanOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(tan(args->operandValues[0]->getDouble()));
}


VentureValuePtr HypotOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(hypot(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble()));
}

VentureValuePtr ExpOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(exp(args->operandValues[0]->getDouble()));
}

VentureValuePtr LogpOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(log(args->operandValues[0]->getDouble()));
}

VentureValuePtr PowOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(pow(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble()));
}

VentureValuePtr SqrtOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureNumber(sqrt(args->operandValues[0]->getDouble()));
}

VentureValuePtr NotOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  return new VentureBool(!args->operandValues[0]->getBool());
}

VentureValuePtr IsSymbolOutputPSP::simulate(Args * args, gsl_rng * rng) const
{
  // TODO not sure if this will work
  return new VentureBool(dynamic_pointer_cast<VentureBool>(args->operandValues[0]));
}
