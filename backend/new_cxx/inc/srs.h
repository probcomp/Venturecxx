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

#ifndef SRS_H
#define SRS_H

#include "types.h"

struct VentureEnvironment;

struct ESR
{
  ESR(FamilyID id,VentureValuePtr exp,shared_ptr<VentureEnvironment> env) :
    id(id), exp(exp), env(env) {};
  FamilyID id;
  VentureValuePtr exp;
  shared_ptr<VentureEnvironment> env;
};

struct LSR { virtual ~LSR() {} };


#endif
