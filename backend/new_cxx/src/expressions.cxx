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

#include "expressions.h"
#include "values.h"

bool isVariable(VentureValuePtr exp)
{
  return dynamic_pointer_cast<VentureSymbol>(exp) != NULL;
}

bool isSelfEvaluating(VentureValuePtr exp)
{
  return !exp->hasArray() || dynamic_pointer_cast<VentureVector>(exp);
}

bool isQuotation(VentureValuePtr exp)
{
  assert(exp->hasArray());
  vector<VentureValuePtr> xs = exp->getArray();
  assert(!xs.empty());
  return xs[0]->hasSymbol() && xs[0]->getSymbol() == "quote";
}

VentureValuePtr textOfQuotation(VentureValuePtr exp)
{
  assert(exp->hasArray());
  vector<VentureValuePtr> xs = exp->getArray();
  assert(!xs.empty());
  return xs[1];
}
