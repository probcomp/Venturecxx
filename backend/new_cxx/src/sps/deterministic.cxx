#include "sps/deterministic.h"
#include <cmath>

VentureValuePtr PlusOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  double sum = 0;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    sum += args->operandValues[i]->getDouble();
  }
  return shared_ptr<VentureNumber>(new VentureNumber(sum));
}

VentureValuePtr MinusOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() - args->operandValues[1]->getDouble()));
}

VentureValuePtr TimesOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
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
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() / args->operandValues[1]->getDouble()));
}

VentureValuePtr EqOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->equals(args->operandValues[1])));
}

VentureValuePtr GtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() > args->operandValues[1]->getDouble()));
}

VentureValuePtr GteOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() >= args->operandValues[1]->getDouble()));
}

VentureValuePtr LtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() < args->operandValues[1]->getDouble()));
}


VentureValuePtr LteOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->getDouble() <= args->operandValues[1]->getDouble()));
}


VentureValuePtr SinOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(sin(args->operandValues[0]->getDouble())));
}


VentureValuePtr CosOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(cos(args->operandValues[0]->getDouble())));
}


VentureValuePtr TanOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(tan(args->operandValues[0]->getDouble())));
}


VentureValuePtr HypotOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(hypot(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble())));
}

VentureValuePtr ExpOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(exp(args->operandValues[0]->getDouble())));
}

VentureValuePtr LogOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(log(args->operandValues[0]->getDouble())));
}

VentureValuePtr PowOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(pow(args->operandValues[0]->getDouble(),args->operandValues[1]->getDouble())));
}

VentureValuePtr SqrtOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureNumber>(new VentureNumber(sqrt(args->operandValues[0]->getDouble())));
}

VentureValuePtr NotOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return shared_ptr<VentureBool>(new VentureBool(!args->operandValues[0]->getBool()));
}

VentureValuePtr IsSymbolOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  // TODO not sure if this will work
  return shared_ptr<VentureBool>(new VentureBool(dynamic_pointer_cast<VentureBool>(args->operandValues[0])));
}
