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

#ifndef PSP_H
#define PSP_H

#include "types.h"
#include "args.h"
#include <cfloat>
#include <gsl/gsl_rng.h>

struct LKernel;
struct ConcreteTrace;
struct ApplicationNode;

struct PSP
{
  virtual VentureValuePtr simulate(
      const boost::shared_ptr<Args> & args, gsl_rng * rng) const =0;
  virtual double logDensity(
      const VentureValuePtr & value,
      const boost::shared_ptr<Args> & args) const =0;
  virtual void incorporate(VentureValuePtr value, boost::shared_ptr<Args> args) const =0;
  virtual void unincorporate(VentureValuePtr value, boost::shared_ptr<Args> args) const =0;

  virtual bool isRandom() const =0;
  virtual bool canAbsorb(
      ConcreteTrace * trace,
      ApplicationNode * appNode,
      Node * parentNode) const =0;

  virtual bool childrenCanAAA() const { return false; }
  virtual boost::shared_ptr<LKernel> const getAAALKernel();

  virtual bool canEnumerateValues(boost::shared_ptr<Args> args) const { return false; }
  virtual vector<VentureValuePtr> enumerateValues(boost::shared_ptr<Args> args) const { return vector<VentureValuePtr>(); }

  virtual double logDensityOfData(boost::shared_ptr<SPAux> spAux) const { assert(false); }
  // TODO variational is punted for now
  // virtual bool hasVariationalLKernel() const { return false; }
  // virtual boost::shared_ptr<LKernel> getVariationalLKernel(ConcreteTrace * trace, Node * node) const;

  // TODO special psp-specific lkernels are punted for now
  virtual bool hasDeltaKernel() const { return false; }
  virtual boost::shared_ptr<LKernel> getDeltaKernel() const { assert(false); return boost::shared_ptr<LKernel>(); }

  /* For slice sampling */
  virtual bool isContinuous() const { return false; }
  virtual double getSupportLowerBound() const { return -FLT_MAX; }
  virtual double getSupportUpperBound() const { return FLT_MAX; }

  virtual PSP* copy_help(ForwardingMap* m) const { return const_cast<PSP*>(this); }

  virtual ~PSP() {}
};

struct DefaultIncorporatePSP : virtual PSP
{
  void incorporate(VentureValuePtr value, boost::shared_ptr<Args> args)
    const {}
  void unincorporate(VentureValuePtr value, boost::shared_ptr<Args> args)
    const {}
};

struct NonAssessablePSP : virtual PSP
{
  bool canAbsorb(
      ConcreteTrace * trace,
      ApplicationNode * appNode,
      Node * node)
    const { return false; }
  double logDensity(
      const VentureValuePtr & value,
      const boost::shared_ptr<Args> & args)
    const { throw "logDensity on non-assessable PSP"; }
};

struct AlwaysAssessablePSP : virtual PSP
{
  bool canAbsorb(
      ConcreteTrace * trace,
      ApplicationNode * appNode,
      Node * node)
    const { return true; }
};

struct TriviallyAssessablePSP : virtual PSP
{
  double logDensity(
      const VentureValuePtr & value,
      const boost::shared_ptr<Args> & args)
    const { return 0; }
};

struct RandomPSP : virtual PSP
  , AlwaysAssessablePSP
{
  bool isRandom() const { return true; }
};

struct DeterministicPSP : virtual PSP
  , DefaultIncorporatePSP
  , NonAssessablePSP
{
  bool isRandom() const { return false; }
};

struct DeterministicMakerAAAPSP : virtual PSP
  , DeterministicPSP
{
};

struct NullRequestPSP : virtual PSP
  , AlwaysAssessablePSP
  , DefaultIncorporatePSP
  , TriviallyAssessablePSP
{
  VentureValuePtr simulate(
      const boost::shared_ptr<Args> & args, gsl_rng * rng) const;
  bool isRandom() const { return false; }
};

struct ESRRefOutputPSP : virtual PSP
  , DefaultIncorporatePSP
  , TriviallyAssessablePSP
{
  VentureValuePtr simulate(
      const boost::shared_ptr<Args> & args, gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace, ApplicationNode * appNode, Node * parentNode) const;
  bool isRandom() const { return false; }
};

#endif
