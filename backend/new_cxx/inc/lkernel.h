// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#ifndef LKERNEL_H
#define LKERNEL_H

#include "types.h"
#include <gsl/gsl_rng.h>

struct Trace;
struct Args;
struct PSP;
struct SP;
struct SPAux;

struct LKernel
{
  virtual VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) =0;
  virtual double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) { return 0; }
  virtual double reverseWeight(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args) 
    { 
      return weight(trace,oldValue,shared_ptr<VentureValue>(),args);
    }
};

struct DefaultAAALKernel : LKernel
{
  // TODO GC this kernel will not outlast the PSP
  DefaultAAALKernel(const PSP * makerPSP): makerPSP(makerPSP) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);

  const PSP * makerPSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValuePtr value, shared_ptr<PSP> psp): value(value), psp(psp) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng);
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args);

  VentureValuePtr value;
  shared_ptr<PSP> psp;
  
};

struct VariationalLKernel : LKernel
{
  virtual vector<double> gradientOfLogDensity(VentureValuePtr value, shared_ptr<Args> args) =0;
  virtual void updateParameters(Gradient gradient,double gain,double stepSize) =0;
};



#endif
