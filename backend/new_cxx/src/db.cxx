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

#include "db.h"

bool DB::hasValue(Node * node) { return values.count(node); }

VentureValuePtr DB::getValue(Node * node)
{
  assert(values.count(node));
  return values[node];
}

void DB::registerValue(Node * node,VentureValuePtr value)
{
  assert(!values.count(node));
  values[node] = value;
}

bool DB::hasLatentDB(Node * makerNode)
{
  return latentDBs.count(makerNode);
}

boost::shared_ptr<LatentDB> DB::getLatentDB(Node * makerNode)
{
  assert(latentDBs.count(makerNode));
  return latentDBs[makerNode];
}

void DB::registerLatentDB(Node * makerNode, boost::shared_ptr<LatentDB> latentDB)
{
  assert(!latentDBs.count(makerNode));
  latentDBs[makerNode] = latentDB;
}

bool DB::hasESRParent(boost::shared_ptr<SP> sp,FamilyID id)
{
  return spFamilyDBs[sp].count(id);
}

RootOfFamily DB::getESRParent(boost::shared_ptr<SP> sp,FamilyID id)
{
  assert(spFamilyDBs[sp].count(id));
  return spFamilyDBs[sp][id];
}

void DB::registerSPFamily(boost::shared_ptr<SP> sp,FamilyID id,RootOfFamily esrParent)
{
  assert(!spFamilyDBs[sp].count(id));
  spFamilyDBs[sp][id] = esrParent;
}

bool DB::hasMadeSPAux(Node * makerNode) { return spAuxs.count(makerNode); }

boost::shared_ptr<SPAux> DB::getMadeSPAux(Node * makerNode)
{
  assert(spAuxs.count(makerNode));
  return spAuxs[makerNode];
}

void DB::registerMadeSPAux(Node * makerNode, boost::shared_ptr<SPAux> spAux)
{
  assert(!spAuxs.count(makerNode));
  spAuxs[makerNode] = spAux;
}
