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

#ifndef SPS_CRP_H
#define SPS_CRP_H

#include "sp.h"
#include "psp.h"
#include "types.h"
#include <stdint.h>

struct CRPSPAux : SPAux
{
  CRPSPAux(): nextIndex(1), numCustomers(0), numTables(0) {}
  SPAux* copy_help(ForwardingMap* m) const { return new CRPSPAux(*this); }
  boost::python::object toPython(Trace * trace) const;

  uint32_t nextIndex;
  uint32_t numCustomers;
  uint32_t numTables;
  map<uint32_t,uint32_t> tableCounts;
};

struct MakeCRPOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  bool childrenCanAAA() const { return true; }
};

struct CRPSP : SP
{
  CRPSP(double alpha, double d);
  boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;

  // for toPython
  const double alpha, d;
};

struct CRPOutputPSP : RandomPSP
{
  CRPOutputPSP(double alpha,double d) : alpha(alpha), d(d) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

  bool canEnumerateValues(shared_ptr<Args> args) const { return true; }
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

 private:
  const double alpha;
  const double d;
};

#endif
