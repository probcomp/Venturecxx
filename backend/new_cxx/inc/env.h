// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

#ifndef ENVIRONMENT_H
#define ENVIRONMENT_H

#include "types.h"
#include "value.h"
#include "values.h"
#include "node.h"

struct VentureEnvironment : VentureValue
{
  VentureEnvironment() {}

  VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv);

  VentureEnvironment(shared_ptr<VentureEnvironment> outerEnv,
		     const vector<shared_ptr<VentureSymbol> > & syms,
		     const vector<Node*> & nodes);

  int getValueTypeRank() const;

  void addBinding(const string& sym,Node * node);
  void removeBinding(const string& sym);
  void replaceBinding(const string& sym,Node * node);
  Node * lookupSymbol(shared_ptr<VentureSymbol> sym);
  Node * lookupSymbol(const string& sym);
  Node * safeLookupSymbol(const string& sym);

  shared_ptr<VentureEnvironment> outerEnv;
  map<string,Node*> frame;

  VentureEnvironment* copy_help(ForwardingMap* m) const;
};

#endif
