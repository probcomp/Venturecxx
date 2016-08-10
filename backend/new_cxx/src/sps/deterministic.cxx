// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "sps/deterministic.h"
#include "utils.h"
#include <cmath>

#include <iostream>
using std::cout;
using std::endl;
VentureValuePtr AddOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  double sum = 0;
  for (size_t i = 0; i < args->operandValues.size(); ++i) {
    sum += args->operandValues[i]->getDouble();
  }
  return shared_ptr<VentureNumber>(new VentureNumber(sum));
}

VentureValuePtr SubOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("minus", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() - args->operandValues[1]->getDouble()));
}

VentureValuePtr MulOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  double prod = 1;
  for (size_t i = 0; i < args->operandValues.size(); ++i) {
    prod *= args->operandValues[i]->getDouble();
  }
  return shared_ptr<VentureNumber>(new VentureNumber(prod));
}


VentureValuePtr DivOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("divide", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(args->operandValues[0]->getDouble() / args->operandValues[1]->getDouble()));
}

VentureValuePtr IntDivOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("integer divide", args, 2);
  return shared_ptr<VentureInteger>(new VentureInteger(args->operandValues[0]->getInt() / args->operandValues[1]->getInt()));
}

VentureValuePtr IntModOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("integer mod", args, 2);
  return shared_ptr<VentureInteger>(new VentureInteger(args->operandValues[0]->getInt() % args->operandValues[1]->getInt()));
}

VentureValuePtr EqOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("equals", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0]->equals(args->operandValues[1])));
}

VentureValuePtr GtOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength(">", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0] > args->operandValues[1]));
}

VentureValuePtr GteOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength(">=", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0] >= args->operandValues[1]));
}

VentureValuePtr LtOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("<", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0] < args->operandValues[1]));
}

VentureValuePtr LteOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("<=", args, 2);
  return shared_ptr<VentureBool>(new VentureBool(args->operandValues[0] <= args->operandValues[1]));
}

VentureValuePtr FloorOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("floor", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(floor(args->operandValues[0]->getDouble())));
}


VentureValuePtr SinOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("sin", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(sin(args->operandValues[0]->getDouble())));
}


VentureValuePtr CosOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("cos", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(cos(args->operandValues[0]->getDouble())));
}


VentureValuePtr TanOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("tan", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(tan(args->operandValues[0]->getDouble())));
}


VentureValuePtr HypotOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("hypot", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(hypot(args->operandValues[0]->getDouble(), args->operandValues[1]->getDouble())));
}

VentureValuePtr ExpOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("exp", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(exp(args->operandValues[0]->getDouble())));
}

VentureValuePtr LogOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("log", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(log(args->operandValues[0]->getDouble())));
}

VentureValuePtr PowOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("pow", args, 2);
  return shared_ptr<VentureNumber>(new VentureNumber(pow(args->operandValues[0]->getDouble(), args->operandValues[1]->getDouble())));
}

VentureValuePtr SqrtOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("sqrt", args, 1);
  return shared_ptr<VentureNumber>(new VentureNumber(sqrt(args->operandValues[0]->getDouble())));
}

VentureValuePtr NotOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("not", args, 1);
  return shared_ptr<VentureBool>(new VentureBool(!args->operandValues[0]->getBool()));
}

VentureValuePtr RealOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("real", args, 1);
  return VentureValuePtr(new VentureNumber(args->operandValues[0]->getDouble()));
}

VentureValuePtr IsNumberOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_number", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureNumber>(args->operandValues[0]) != NULL));
}

VentureValuePtr IsBoolOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_boolean", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureBool>(args->operandValues[0]) != NULL));
}

VentureValuePtr IsSymbolOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_symbol", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureSymbol>(args->operandValues[0]) != NULL));
}

VentureValuePtr AtomOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("atom", args, 1);
  return VentureValuePtr(new VentureAtom(args->operandValues[0]->getInt()));
}

VentureValuePtr AtomIndexOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("atom_index", args, 1);
  return VentureValuePtr(new VentureInteger(args->operandValues[0]->getAtom()));
}

VentureValuePtr IsAtomOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_atom", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureAtom>(args->operandValues[0]) != NULL));
}

VentureValuePtr IntegerOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("integer", args, 1);
  return VentureValuePtr(new VentureInteger(args->operandValues[0]->getDouble()));
}

VentureValuePtr IsIntegerOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_integer", args, 1);
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureInteger>(args->operandValues[0]) != NULL));
}

VentureValuePtr ProbabilityOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("probability", args, 1);
  return VentureValuePtr(new VentureNumber(args->operandValues[0]->getProbability()));
}

VentureValuePtr IsProbabilityOutputPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("is_probability", args, 1);
  if (args->operandValues[0]->hasDouble()) {
    double x = args->operandValues[0]->getDouble();
    return VentureValuePtr(new VentureBool(0 <= x && x <= 1));
  } else {
    return VentureValuePtr(new VentureBool(false));
  }
}
