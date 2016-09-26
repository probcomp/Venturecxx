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

#ifndef REGEN_H
#define REGEN_H

#include "types.h"

struct Trace;
struct Scaffold;
struct DB;
struct ApplicationNode;
struct OutputNode;
struct RequestNode;
struct VentureEnvironment;

double regenAndAttach(
    Trace * trace,
    const vector<Node*> & border,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double constrain(
    Trace * trace, OutputNode * node, const VentureValuePtr & value);



void propagateConstraint(
    Trace * trace, Node * node, const VentureValuePtr & value);

double attach(
    Trace * trace,
    ApplicationNode * node,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double regen(
    Trace * trace,
    Node * node,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double regenParents(
    Trace * trace,
    Node * node,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double regenESRParents(
    Trace * trace,
    Node * node,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

pair<double, Node*> evalFamily(
    Trace * trace,
    const VentureValuePtr & exp,
    const shared_ptr<VentureEnvironment> & env,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);


double apply(
    Trace * trace,
    RequestNode * requestNode,
    OutputNode * outputNode,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);


void processMadeSP(
    Trace * trace,
    Node * node,
    bool isAAA,
    bool shouldRestore,
    const shared_ptr<DB> & db);

double applyPSP(
    Trace * trace,
    ApplicationNode * node,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double evalRequests(
    Trace * trace,
    RequestNode * requestNode,
    const shared_ptr<Scaffold> & scaffold,
    bool shouldRestore,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);

double restore(
    Trace * trace,
    Node * node,
    const shared_ptr<Scaffold> & scaffold,
    const shared_ptr<DB> & db,
    const shared_ptr<map<Node*, Gradient> > & gradients);


#endif
