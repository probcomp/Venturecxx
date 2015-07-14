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
  virtual VentureValuePtr simulate(boost::shared_ptr<Args> args,gsl_rng * rng) const =0;
  virtual double logDensity(VentureValuePtr value,boost::shared_ptr<Args> args) const { return 0; }
  virtual void incorporate(VentureValuePtr value,boost::shared_ptr<Args> args) const {}
  virtual void unincorporate(VentureValuePtr value,boost::shared_ptr<Args> args) const {}

  virtual bool isRandom() const { return false; }
  virtual bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return false; }

  virtual bool childrenCanAAA() const { return false; }
  virtual boost::shared_ptr<LKernel> const getAAALKernel();

  virtual bool canEnumerateValues(boost::shared_ptr<Args> args) const { return false; }
  virtual vector<VentureValuePtr> enumerateValues(boost::shared_ptr<Args> args) const { return vector<VentureValuePtr>(); }

  virtual double logDensityOfCounts(boost::shared_ptr<SPAux> spAux) const { assert(false); }
  // TODO variational is punted for now
  // virtual bool hasVariationalLKernel() const { return false; }
  // virtual boost::shared_ptr<LKernel> getVariationalLKernel(ConcreteTrace * trace,Node * node) const;

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

struct NullRequestPSP : PSP
{
  VentureValuePtr simulate(boost::shared_ptr<Args> args,gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return true; }
};

struct ESRRefOutputPSP : PSP
{
  VentureValuePtr simulate(boost::shared_ptr<Args> args,gsl_rng * rng) const;
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const;
};

struct RandomPSP : PSP
{
  bool isRandom() const { return true; }
  bool canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const { return true; }
};

#endif
