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

#ifndef SERIALIZE_H
#define SERIALIZE_H

#include "types.h"
#include "db.h"

struct Trace;

struct OrderedDB : DB
{
  bool hasValue(Node * node);
  VentureValuePtr getValue(Node * node);
  void registerValue(Node * node, VentureValuePtr value);

  OrderedDB(Trace * trace, vector<VentureValuePtr> values);
  OrderedDB(Trace * trace);
  vector<VentureValuePtr> listValues() { return stack; }

private:
  Trace * trace;
  vector<VentureValuePtr> stack;
};

#endif
