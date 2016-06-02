// Copyright (c) 2014, 2016 MIT Probabilistic Computing Project.
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

#ifndef DIR_MULT_H
#define DIR_MULT_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"
#include "stop-and-copy.h"

// Collapsed SPAux
struct DirCatSPAux : SPAux
{
  DirCatSPAux(int n) : counts(n, 0), total(0) {}
  vector<int> counts;
  int total;
  DirCatSPAux* copy_help(ForwardingMap* m) const;
  boost::python::object toPython(Trace * trace) const;
};

// Collapsed Asymmetric
struct MakeDirCatOutputPSP : virtual PSP
  , DeterministicMakerAAAPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct DirCatOutputPSP : RandomPSP
{
  DirCatOutputPSP(const vector<double>& alpha, double total):
    alpha(alpha), total(total) {}

  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void incorporate(VentureValuePtr value, shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value, shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

  double logDensityOfData(shared_ptr<SPAux> spAux) const;

private:
  const vector<double> alpha;
  const double total;
};

// Collapsed Symmetric
struct MakeSymDirCatOutputPSP : virtual PSP
  , DeterministicMakerAAAPSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct SymDirCatSP : SP
{
  SymDirCatSP(double alpha, size_t n);
  boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;

  // for toPython
  const double alpha;
  const size_t n;
};

// Uncollapsed SPAux
struct UCDirCatSPAux : DirCatSPAux
{
  UCDirCatSPAux(int n): DirCatSPAux(n), theta(n, 0) {}
  UCDirCatSPAux* copy_help(ForwardingMap* m) const;
  vector<double> theta;
};

// Uncollapsed Asymmetric
struct MakeUCDirCatOutputPSP : virtual RandomPSP
  , DefaultIncorporatePSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
};

struct UCDirCatSP : SP
{
  UCDirCatSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP, outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,
               gsl_rng * rng) const;
  UCDirCatSP* copy_help(ForwardingMap* m) const;
};

struct UCDirCatOutputPSP : RandomPSP
{
  UCDirCatOutputPSP(size_t n) : n(n) {}

  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
  void incorporate(VentureValuePtr value, shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value, shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

private:
  const size_t n;
};

// Uncollapsed Symmetric
struct MakeUCSymDirCatOutputPSP : virtual RandomPSP
  , DefaultIncorporatePSP
{
  VentureValuePtr simulate(const shared_ptr<Args> & args, gsl_rng * rng) const;
  double logDensity(
      const VentureValuePtr & value,
      const shared_ptr<Args> & args) const;
};

struct UCSymDirCatSP : SP
{
  UCSymDirCatSP(PSP * requestPSP, PSP * outputPSP):
    SP(requestPSP, outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,
               gsl_rng * rng) const;
  UCSymDirCatSP* copy_help(ForwardingMap* m) const;
};

#endif
