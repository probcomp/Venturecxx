// Copyright (c) 2013, 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

#ifndef SP_H
#define SP_H

#include "types.h"
#include "args.h"
#include "value.h"
#include <map>

#include <gsl/gsl_rng.h>

struct SPAux;
struct LSR;
struct LatentDB;
struct PSP;
struct ApplicationNode;
struct RequestNode;
struct OutputNode;
struct Args;

struct VentureSPRef : VentureValue
{
  VentureSPRef(Node * makerNode): makerNode(makerNode) {}
  Node * makerNode;

  int getValueTypeRank() const;
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;

  VentureSPRef* copy_help(ForwardingMap* m) const;
};

struct SPFamilies
{
  SPFamilies() {}
  SPFamilies(const MapVVPtrRootOfFamily & families): families(families) {}

  MapVVPtrRootOfFamily families;
  bool containsFamily(const FamilyID & id);
  RootOfFamily getRootOfFamily(const FamilyID & id);
  void registerFamily(const FamilyID & id, const RootOfFamily & root);
  void unregisterFamily(const FamilyID & id);
  SPFamilies* copy_help(ForwardingMap* m) const;
};

struct SPAux
{
  virtual ~SPAux() {}
  boost::shared_ptr<SPAux> clone();
  virtual boost::python::object toPython(Trace * trace) const;
  virtual VentureValuePtr asVentureValue() const;
  virtual SPAux* copy_help(ForwardingMap* m) const = 0;
};

struct SP
{
  SP(PSP * requestPSP, PSP * outputPSP);

  boost::shared_ptr<PSP> requestPSP;
  boost::shared_ptr<PSP> outputPSP;

  virtual boost::shared_ptr<PSP> getPSP(ApplicationNode * node) const;

  virtual boost::shared_ptr<LatentDB> constructLatentDB() const;
  virtual double simulateLatents(boost::shared_ptr<Args> args,
                                 boost::shared_ptr<LSR> lsr,
                                 bool shouldRestore,
                                 boost::shared_ptr<LatentDB> latentDB,
                                 gsl_rng * rng) const;
  virtual double detachLatents(boost::shared_ptr<Args> args,
                               boost::shared_ptr<LSR> lsr,
                               boost::shared_ptr<LatentDB> latentDB) const;
  virtual bool hasAEKernel() const { return false; }
  virtual void AEInfer(boost::shared_ptr<SPAux> spAux,
                       boost::shared_ptr<Args> args, gsl_rng * rng) const;

  virtual boost::python::dict toPython(Trace * trace,
                                       boost::shared_ptr<SPAux> spAux) const;
  virtual SP* copy_help(ForwardingMap* m) const;
  virtual ~SP() {}
};

#endif
