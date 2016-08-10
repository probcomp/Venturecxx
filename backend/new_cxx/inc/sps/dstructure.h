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

#ifndef SPS_DSTRUCTURE_H
#define SPS_DSTRUCTURE_H

#include "psp.h"

struct SimplexOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsSimplexOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ToSimplexOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

/* Polymorphic operators */

struct LookupOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ContainsOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct SizeOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};


/* Dicts */

struct DictOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsDictOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

/* Arrays */

struct ArrayOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ToArrayOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct PrependOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct AppendOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ConcatOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsArrayOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};


/* Lists */

struct PairOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IsPairOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ListOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct FirstOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct SecondOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

// TODO ought to allow dotted lists
struct RestOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

/* Functional */

struct ApplyRequestPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct FixRequestPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct FixOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ArrayMapRequestPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct IndexedArrayMapRequestPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ESRArrayOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct ArangeOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

struct RepeatOutputPSP : virtual PSP
  , DeterministicPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
};

#endif
