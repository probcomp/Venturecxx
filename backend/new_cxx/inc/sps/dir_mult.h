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

#ifndef DIR_MULT_H
#define DIR_MULT_H

#include "types.h"
#include "psp.h"
#include "args.h"
#include "sp.h"
#include "stop-and-copy.h"

// Collapsed SPAux
struct DirMultSPAux : SPAux
{
  DirMultSPAux(int n) : counts(n, 0), total(0) {}
  vector<int> counts;
  int total;
  DirMultSPAux* copy_help(ForwardingMap* m) const;
  boost::python::object toPython(Trace * trace) const;
};

// Collapsed Symmetric

struct MakeSymDirMultOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct SymDirMultSP : SP
{
  SymDirMultSP(double alpha, size_t n);
  boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;

  // for toPython
  const double alpha;
  const size_t n;
};

struct SymDirMultOutputPSP : RandomPSP
{
  SymDirMultOutputPSP(double alpha, size_t n) : alpha(alpha), n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

private:
  const double alpha;
  const size_t n;
};

// Collapsed Asymmetric
struct MakeDirMultOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct DirMultOutputPSP : RandomPSP
{
  DirMultOutputPSP(const vector<double>& alpha, double total) : alpha(alpha), total(total) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

private:
  const vector<double> alpha;
  const double total;
};

// Uncollapsed SPAux
struct UCDirMultSPAux : DirMultSPAux
{
  UCDirMultSPAux(int n): DirMultSPAux(n), theta(n,0) {}
  UCDirMultSPAux* copy_help(ForwardingMap* m) const;
  vector<double> theta;
};

// Uncollapsed Symmetric
struct MakeUCSymDirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UCSymDirMultSP : SP
{
  UCSymDirMultSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const;
};

struct UCSymDirMultOutputPSP : RandomPSP
{
  UCSymDirMultOutputPSP(size_t n) : n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

private:
  const size_t n;
};

// Uncollapsed Asymmetric
struct MakeUCDirMultOutputPSP : RandomPSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;
};

struct UCDirMultSP : SP
{
  UCDirMultSP(PSP * requestPSP, PSP * outputPSP): SP(requestPSP,outputPSP) {}

  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,gsl_rng * rng) const;
};

struct UCDirMultOutputPSP : RandomPSP
{
  UCDirMultOutputPSP(size_t n) : n(n) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

private:
  const size_t n;
};


#endif
