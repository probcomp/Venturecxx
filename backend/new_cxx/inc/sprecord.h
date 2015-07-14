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

#ifndef SP_RECORD_H
#define SP_RECORD_H

#include "types.h"
#include "sp.h"

struct ConcreteTrace;

struct VentureSPRecord : VentureValue
{
  VentureSPRecord(SP * sp): sp(sp), spFamilies(new SPFamilies()) {}
  VentureSPRecord(boost::shared_ptr<SP> sp): sp(sp), spFamilies(new SPFamilies()) {}
  VentureSPRecord(SP * sp,SPAux * spAux): sp(sp), spAux(spAux), spFamilies(new SPFamilies()) {}
  VentureSPRecord(boost::shared_ptr<SP> sp,boost::shared_ptr<SPAux> spAux): sp(sp), spAux(spAux), spFamilies(new SPFamilies()) {}

  boost::shared_ptr<SP> sp;
  boost::shared_ptr<SPAux> spAux;
  boost::shared_ptr<SPFamilies> spFamilies;

  boost::shared_ptr<SPAux> getSPAux() const { return spAux; }

  int getValueTypeRank() const;
  bool equals(const VentureValuePtr & other) const;
  size_t hash() const;
  boost::python::dict toPython(Trace * trace) const;
  string toString() const;

  VentureSPRecord* copy_help(ForwardingMap* m) const;
};


#endif
