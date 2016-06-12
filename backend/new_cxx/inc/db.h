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

#ifndef DB_H
#define DB_H

#include "types.h"

struct OutputNode;
struct SPAux;
struct SP;
struct Node;

struct LatentDB { virtual ~LatentDB() {}; };

struct DB
{
  virtual bool hasValue(Node * node);
  virtual VentureValuePtr getValue(Node * node);
  virtual void registerValue(Node * node, const VentureValuePtr & value);

  bool hasLatentDB(Node * makerNode);
  shared_ptr<LatentDB> getLatentDB(Node * makerNode);
  void registerLatentDB(
      Node * makerNode, const shared_ptr<LatentDB> & latentDB);

  bool hasESRParent(const shared_ptr<SP> & sp, const FamilyID & id);
  RootOfFamily getESRParent(const shared_ptr<SP> & sp, const FamilyID & id);
  void registerSPFamily(
      const shared_ptr<SP> & sp,
      const FamilyID & id,
      const RootOfFamily & esrParent);

  bool hasMadeSPAux(Node * makerNode);
  shared_ptr<SPAux> getMadeSPAux(Node * makerNode);
  void registerMadeSPAux(Node * makerNode, const shared_ptr<SPAux> & spAux);

private:
  map<Node*, shared_ptr<LatentDB> > latentDBs;
  map<Node*, VentureValuePtr> values;
  map<shared_ptr<SP>, map<FamilyID, RootOfFamily> > spFamilyDBs;
  map<Node*, shared_ptr<SPAux> > spAuxs;
};

#endif
