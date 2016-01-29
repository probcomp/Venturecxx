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

#include "pyutils.h"
#include "values.h"

#include <iostream>

#include <boost/python/numeric.hpp>

using std::cout;
using std::endl;

using namespace boost::python;
using boost::python::str;

VentureValuePtr parseList(object value)
{
  extract<list> getList(value);
  if (!getList.check()) throw "Not a list: " + str(value);
  list l = getList();

  ssize_t size = len(l);
  VentureValuePtr tail = VentureValuePtr(new VentureNil());

  for (ssize_t i = size - 1; i >= 0; --i)
  {
    VentureValuePtr item = parseValue(extract<dict>(l[i]));
    tail = VentureValuePtr(new VenturePair(item, tail));
  }

  return tail;
}

VentureValuePtr parseImproperList(object value)
{
  extract<list> getList(value[0]);
  if (!getList.check()) throw "Not a list: " + str(value[0]);
  list l = getList();

  ssize_t size = len(l);
  VentureValuePtr tail = parseValue(extract<dict>(value[1]));

  for (ssize_t i = size - 1; i >= 0; --i)
  {
    VentureValuePtr item = parseValue(extract<dict>(l[i]));
    tail = VentureValuePtr(new VenturePair(item, tail));
  }

  return tail;
}

VentureValuePtr parseArray(object value)
{
  extract<list> getList(value);
  if (!getList.check()) throw "Not a list: " + str(value);
  list l = getList();

  ssize_t size = len(l);
  vector<VentureValuePtr> v;

  for (ssize_t i = 0; i < size; ++i)
  {
    v.push_back(parseValue(extract<dict>(l[i])));
  }

  return VentureValuePtr(new VentureArray(v));
}

// TODO: Puma doesn't have general unboxed arrays, because this
// involves complication with types and templates.
// For now, support only numeric unboxed arrays backed by VectorXd.
VentureValuePtr parseVector(object value);
VentureValuePtr parseArrayUnboxed(object value, object subtype)
{

  return parseVector(value);
}

VentureValuePtr parseSimplex(object value)
{
  extract<numeric::array> getNumpyArray(value);
  list l;
  if (getNumpyArray.check())
  {
    l = list(getNumpyArray());
  }
  else
  {
    extract<list> getList(value);
    if (!getList.check()) { throw "Simplex must be a list or numpy array."; }
    l = getList();
  }

  ssize_t size = len(l);
  Simplex s;

  for (ssize_t i = 0; i < size; ++i)
  {
    s.push_back(extract<double>(l[i]));
  }

  return VentureValuePtr(new VentureSimplex(s));
}

VentureValuePtr parseVector(object value)
{
  extract<numeric::array> getNumpyArray(value);
  list l;
  if (getNumpyArray.check())
  {
    l = list(getNumpyArray());
  }
  else
  {
    extract<list> getList(value);
    if (!getList.check()) { throw "Vector must be a list or numpy array."; }
    l = getList();
  }

  ssize_t size = len(l);
  VectorXd v(size);

  for (ssize_t i = 0; i < size; ++i)
  {
    v[i] = extract<double>(l[i]);
  }

  return VentureValuePtr(new VentureVector(v));
}

VentureValuePtr parseDict(object value)
{
  extract<list> getItems(value);

  if (!getItems.check()) { throw "Dict value must be a list."; }

  list items = getItems();
  ssize_t size = len(items);

  MapVVPtrVVPtr m;

  for (ssize_t i = 0; i < size; ++i)
  {
    extract<tuple> getPair(items[i]);
    if (!getPair.check()) { throw "Dict item must be a pair."; }

    tuple pair = getPair();

    VentureValuePtr k = parseValue(extract<dict>(pair[0]));
    VentureValuePtr v = parseValue(extract<dict>(pair[1]));

    m[k] = v;
  }

  return VentureValuePtr(new VentureDictionary(m));
}

VentureValuePtr parseMatrix(object value)
{
  extract<numeric::array> getNumpyArray(value);
  if (!getNumpyArray.check())
  {
    throw "Matrix must be represented as a numpy array.";
  }

  numeric::array data = getNumpyArray();
  tuple shape = extract<tuple>(data.attr("shape"));

  if (len(shape) != 2) { throw "Matrix must be two-dimensional."; }
  size_t rows = extract<size_t>(shape[0]);
  size_t cols = extract<size_t>(shape[1]);

  MatrixXd M(rows,cols);

  for (size_t i = 0; i < rows; ++i)
  {
    for (size_t j = 0; j < cols; ++j)
    {
      M(i,j) = extract<double>(data[make_tuple(i, j)]);
    }
  }
  return VentureValuePtr(new VentureMatrix(M));
}

VentureValuePtr parseSymmetricMatrix(object value)
{
  return VentureValuePtr(
    new VentureSymmetricMatrix(parseMatrix(value)->getSymmetricMatrix()));
}

VentureValuePtr parseValueO(object o)
{
  extract<dict> d(o);
  return parseValue(d);
}

VentureValuePtr parseValue(dict d)
{
  string type = extract<string>(d["type"]);

  object value = d["value"];

  if (type == "number")
  {
    return VentureValuePtr(new VentureNumber(extract<double>(value)));
  }
  else if (type == "real")
  {
    return VentureValuePtr(new VentureNumber(extract<double>(value)));
  }
  else if (type == "integer") {
    // The parser currently makes these be Python floats
    extract<int> i(value);
    if (i.check()) { return VentureValuePtr(new VentureInteger(i)); }
    extract<double> d(value);
    if (d.check())
    {
      return VentureValuePtr(new VentureInteger((int)round(d)));
    }
    throw "Unknown format for integer";
  }
  else if (type == "probability")
  {
    return VentureValuePtr(new VentureProbability(extract<double>(value)));
  }
  else if (type == "atom")
  {
    return VentureValuePtr(new VentureAtom(extract<int32_t>(value)));
  }
  else if (type == "boolean")
  {
    return VentureValuePtr(new VentureBool(extract<bool>(value)));
  }
  else if (type == "symbol")
  {
    return VentureValuePtr(new VentureSymbol(extract<string>(value)));
  }
  else if (type == "string")
  {
    return VentureValuePtr(new VentureString(extract<string>(value)));
  }
  else if (type == "list") { return parseList(value); }
  else if (type == "improper_list") { return parseImproperList(value); }
  else if (type == "vector") { return parseVector(value); }
  else if (type == "array") { return parseArray(value); }
  else if (type == "array_unboxed")
  {
    return parseArrayUnboxed(value, d["subtype"]);
  }
  else if (type == "simplex") { return parseSimplex(value); }
  else if (type == "dict") { return parseDict(value); }
  else if (type == "matrix") { return parseMatrix(value); }
  else if (type == "symmetric_matrix") { return parseSymmetricMatrix(value); }
  else { throw "Unknown type '" + type + "'"; }
}

VentureValuePtr parseExpression(object o)
{
  extract<dict> getDict(o);
  if (getDict.check()) { return VentureValuePtr(parseValue(getDict())); }

  extract<list> getList(o);
  assert(getList.check());

  list l = getList();

  vector<VentureValuePtr> exp;

  ssize_t L = len(l);

  for(ssize_t i=0; i<L; ++i)
  {
    exp.push_back(parseExpression(l[i]));
  }
  return VentureValuePtr(new VentureArray(exp));
}
