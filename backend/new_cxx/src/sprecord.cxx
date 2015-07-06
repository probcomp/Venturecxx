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

#include "sprecord.h"

// TODO hacky
bool VentureSPRecord::equals(const VentureValuePtr & other) const
{
  boost::shared_ptr<VentureSPRecord> other_v = dynamic_pointer_cast<VentureSPRecord>(other);
  return other_v && (other_v->sp.get() == sp.get());
}

size_t VentureSPRecord::hash() const 
{ 
  boost::hash<long> long_hash;
  return long_hash(reinterpret_cast<long>(sp.get()));
}

boost::python::dict VentureSPRecord::toPython(Trace * trace) const
{
  return sp->toPython(trace, spAux);
}

string VentureSPRecord::toString() const { return "spRecord"; }
