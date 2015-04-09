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

#include "value.h"
#include "values.h"
#include "sp.h"
#include "sprecord.h"
#include "env.h"
#include <boost/lexical_cast.hpp>

int getValueTypeRank(const VentureValue * v);
void cannotConvertType(const VentureValue * obj, string target)
{
  throw "Cannot convert " + obj->toString() + " to [" + target + "]";
}

bool VentureValue::hasDouble() const { return false; }

double VentureValue::getDouble() const
{
  cannotConvertType(this,"double"); assert(false); throw "no return";
}

bool VentureValue::hasInt() const { return false; }
long VentureValue::getInt() const
{
  cannotConvertType(this,"int"); assert(false); throw "no return";
}

double VentureValue::getProbability() const
{
  double x;
  try {
    x = getDouble();
  }
  catch (string) {
    cannotConvertType(this,"probability"); assert(false); throw "no return";
  }
  if (0 <= x && x <= 1) {
    return x;
  }
  else {
    throw "Probability out of range " + toString();
  }
}

int VentureValue::getAtom() const
{
  cannotConvertType(this,"atom"); assert(false); throw "no return";
}

bool VentureValue::isBool() const { return false; }
bool VentureValue::getBool() const
{
  cannotConvertType(this,"bool"); assert(false); throw "no return";
}

bool VentureValue::hasSymbol() const { return false; }
const string& VentureValue::getSymbol() const
{
  cannotConvertType(this,"symbol"); assert(false); throw "no return";
}


const VentureValuePtr& VentureValue::getFirst() const
{
  cannotConvertType(this,"pair"); assert(false); throw "no return";
}

const VentureValuePtr& VentureValue::getRest() const
{
  cannotConvertType(this,"pair"); assert(false); throw "no return";
}

  
vector<VentureValuePtr> VentureValue::getArray() const
{
  cannotConvertType(this,"array"); assert(false); throw "no return";
}

const Simplex& VentureValue::getSimplex() const
{
  cannotConvertType(this,"simplex"); assert(false); throw "no return";
}

const MapVVPtrVVPtr& VentureValue::getDictionary() const
{
  cannotConvertType(this,"dictionary"); assert(false); throw "no return";
}

VectorXd VentureValue::getVector() const
{
  cannotConvertType(this,"vector"); assert(false); throw "no return";
}


MatrixXd VentureValue::getMatrix() const
{
  cannotConvertType(this,"matrix"); assert(false); throw "no return";
}

MatrixXd VentureValue::getSymmetricMatrix() const
{
  MatrixXd m = getMatrix();
  if (m.isApprox(m.transpose())) {
    return m;
  }
  else {
    throw "Matrix is not symmetric " + toString();
  }
}


boost::python::dict VentureValue::toPython(Trace * trace) const
{ 
  boost::python::dict value;
  value["type"] = "unknown";
  value["value"] = "opaque";
  return value;
}


bool VentureValue::operator<(const VentureValuePtr & rhs) const 
{
  int t1 = getValueTypeRank();
  int t2 = rhs->getValueTypeRank();
  if (t1 < t2) { return true; }
  else if (t2 < t1) { return false; }
  else { return ltSameType(rhs); }
}

int VentureValue::getValueTypeRank() const { throw "Cannot compare type " + toString(); }

bool VentureValue::ltSameType(const VentureValuePtr & rhs) const { throw "Cannot compare " + toString(); }


bool VentureValue::equals(const VentureValuePtr & other) const 
{
  int t1 = getValueTypeRank();
  int t2 = other->getValueTypeRank();
  if (t1 != t2) { return false; }
  else { return equalsSameType(other); }
}

bool VentureValue::equalsSameType(const VentureValuePtr & rhs) const { throw "Cannot compare " + toString(); }

size_t VentureValue::hash() const
{
  assert(false); assert(false); throw "no return";
}

VentureValuePtr VentureValue::lookup(VentureValuePtr index) const { throw "Cannot look things up in " + toString(); }
bool VentureValue::contains(VentureValuePtr index) const { throw "Cannot look for things in " + toString(); }
int VentureValue::size() const { throw "Cannot measure size of " + toString(); }


const vector<ESR>& VentureValue::getESRs() const
{
  cannotConvertType(this,"requests"); assert(false); throw "no return";
}

const vector<shared_ptr<LSR> >& VentureValue::getLSRs() const
{
  cannotConvertType(this,"requests"); assert(false); throw "no return";
}


Node * VentureValue::getNode() const
{
  cannotConvertType(this,"node") ; assert(false); throw "no return";
}


shared_ptr<SPAux> VentureValue::getSPAux() const
{
  cannotConvertType(this,"sprecord") ; assert(false); throw "no return";
}

string VentureValue::asExpression() const { return toString(); }
