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

#ifndef ARGS_H
#define ARGS_H

#include "types.h"
#include "values.h"

struct Trace;
struct ApplicationNode;
struct RequestNode;
struct VentureRequest;
struct SPAux;
struct VentureEnvironment;

struct Args
{
  Args(Trace * trace, ApplicationNode * node);

  Trace * _trace;
  ApplicationNode * node;
  vector<VentureValuePtr> operandValues;
  vector<Node*> operandNodes;

  boost::shared_ptr<VentureRequest> requestValue;
  RequestNode * requestNode;

  vector<VentureValuePtr> esrParentValues;
  vector<RootOfFamily> esrParentNodes;

  boost::shared_ptr<SPAux> spAux;
  boost::shared_ptr<SPAux> aaaMadeSPAux;

  boost::shared_ptr<VentureEnvironment> env;

};

#endif
