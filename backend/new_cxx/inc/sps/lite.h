// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

#ifndef SPS_LITE_H
#define SPS_LITE_H

#include <boost/python.hpp>
#include <boost/python/object.hpp>

#include "types.h"
#include "sp.h"
#include "psp.h"
#include "lkernel.h"
#include "db.h"

// A mechanism for calling foreign SPs (written in Python, using the
// Lite interface) in Puma. Implemented as a Puma SP which wraps a
// ForeignLiteSP object (defined in lite/foreign.py), which in turn
// wraps a Lite SP. The Puma half handles value translation from C++
// to stack dicts, while the Lite half handles value translation from
// stack dicts to Lite VentureValues.

struct ForeignLitePSP : PSP
{
  ForeignLitePSP(boost::python::object psp): psp(psp) {}

  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
  double logDensity(VentureValuePtr value, shared_ptr<Args> args) const;

  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  bool isRandom() const;
  bool canAbsorb(ConcreteTrace * trace, ApplicationNode * appNode,
                 Node * parentNode) const;

  bool childrenCanAAA() const;
  shared_ptr<LKernel> const getAAALKernel();

  bool canEnumerateValues(shared_ptr<Args> args) const;
  vector<VentureValuePtr> enumerateValues(shared_ptr<Args> args) const;

  double logDensityOfCounts(shared_ptr<SPAux> spAux) const;

  boost::python::object psp;
};

struct ForeignLiteSPAux : SPAux
{
  ForeignLiteSPAux(boost::python::object aux): aux(aux) {}
  SPAux* copy_help(ForwardingMap* m) const {
    return new ForeignLiteSPAux(aux.attr("copy")()); }
  boost::python::object aux;
};

struct ForeignLiteLKernel : LKernel
{
  ForeignLiteLKernel(boost::python::object lkernel): lkernel(lkernel) {}
  VentureValuePtr forwardSimulate(Trace * trace, VentureValuePtr oldValue,
                                  shared_ptr<Args> args,gsl_rng * rng);
  double forwardWeight(Trace * trace, VentureValuePtr newValue,
                       VentureValuePtr oldValue,shared_ptr<Args> args);
  double reverseWeight(Trace * trace, VentureValuePtr oldValue,
                       shared_ptr<Args> args);

  boost::python::object lkernel;
};

struct ForeignLiteLSR : LSR
{
  ForeignLiteLSR(boost::python::object lsr): lsr(lsr) {}

  boost::python::object lsr;
};

struct ForeignLiteLatentDB : LatentDB
{
  ForeignLiteLatentDB(boost::python::object latentDB): latentDB(latentDB) {}

  boost::python::object latentDB;
};

struct ForeignLiteRequest : VentureRequest
{
  ForeignLiteRequest(const vector<ESR> & esrs,
                     const vector<shared_ptr<LSR> > & lsrs):
    VentureRequest(esrs, lsrs) {}
  ForeignLiteRequest(const vector<shared_ptr<LSR> > & lsrs):
    VentureRequest(lsrs) {}
  boost::python::dict toPython(Trace * trace) const;
};

struct ForeignLiteSP : SP
{
  // TODO: requestPSP (needs requests to be stackable)
  ForeignLiteSP(boost::python::object sp):
    SP(new ForeignLitePSP(sp.attr("requestPSP")),
       new ForeignLitePSP(sp.attr("outputPSP"))),
    sp(sp) {}

  shared_ptr<LatentDB> constructLatentDB() const;
  double simulateLatents(shared_ptr<Args> args, shared_ptr<LSR> lsr,
                         bool shouldRestore, shared_ptr<LatentDB> latentDB,
                         gsl_rng * rng) const;
  double detachLatents(shared_ptr<Args> args, shared_ptr<LSR> lsr,
                       shared_ptr<LatentDB> latentDB) const;

  bool hasAEKernel() const;
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args,
               gsl_rng * rng) const;

  boost::python::dict toPython(Trace * trace, shared_ptr<SPAux> spAux) const;

  boost::python::object sp;
};

#endif
