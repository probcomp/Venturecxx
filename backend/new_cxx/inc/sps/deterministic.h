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

#ifndef DETERMINISTIC_PSPS_H
#define DETERMINISTIC_PSPS_H

#include "psp.h"
#include "args.h"

struct AddOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct SubOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct MulOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct DivOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IntDivOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IntModOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct EqOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct GtOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct GteOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct LtOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct LteOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct FloorOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct SinOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct CosOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct TanOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct HypotOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ExpOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct LogOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct PowOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct SqrtOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct NotOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct RealOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsNumberOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsBoolOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsSymbolOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct AtomOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct AtomIndexOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsAtomOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IntegerOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsIntegerOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ProbabilityOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsProbabilityOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

#endif
