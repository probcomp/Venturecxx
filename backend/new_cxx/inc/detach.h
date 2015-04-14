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

#ifndef DETACH_H
#define DETACH_H

#include "types.h"

struct ConcreteTrace;
struct Scaffold;
struct DB;
struct Node;
struct ApplicationNode;
struct OutputNode;
struct RequestNode;

pair<double,shared_ptr<DB> > detachAndExtract(ConcreteTrace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold);
double unconstrain(ConcreteTrace * trace,OutputNode * node);
double detach(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extractParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extractESRParents(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double extract(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unevalFamily(ConcreteTrace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unapply(ConcreteTrace * trace,OutputNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
void teardownMadeSP(ConcreteTrace * trace,Node * node,bool isAAA,shared_ptr<DB> db);
double unapplyPSP(ConcreteTrace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);
double unevalRequests(ConcreteTrace * trace,RequestNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db);

#endif
