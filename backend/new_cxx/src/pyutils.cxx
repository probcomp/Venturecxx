#include "pyutils.h"
#include "values.h"

#include <iostream>

using std::cout;
using std::endl;

VentureValuePtr parseSimplex(boost::python::dict d)
{
  boost::python::extract<boost::python::list> getList(d["value"]);
  if (!getList.check()) { throw "Simplex point must be a list."; }
  
  boost::python::list l = getList();
  
  boost::python::ssize_t len = boost::python::len(l);
  Simplex s;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    s.push_back(boost::python::extract<double>(l[i]));
  }
  
  return VentureValuePtr(new VentureSimplex(s));
}

VentureValuePtr parseArray(boost::python::dict d)
{
  boost::python::extract<boost::python::list> getList(d["value"]);
  if (!getList.check()) { throw "Array must be a list."; }
  
  boost::python::list l = getList();
  
  boost::python::ssize_t len = boost::python::len(l);
  vector<VentureValuePtr> v;
  
  for (boost::python::ssize_t i = 0; i < len; ++i)
  {
    v.push_back(parseValue(boost::python::extract<boost::python::dict>(l[i])));
  }
  
  return VentureValuePtr(new VentureArray(v));
}

VentureValuePtr parseValue(boost::python::dict d)
{
  string type = boost::python::extract<string>(d["type"]);
  if (type == "boolean") { return shared_ptr<VentureBool>(new VentureBool(boost::python::extract<bool>(d["value"]))); }
  else if (type == "number" || type == "real") { return shared_ptr<VentureNumber>(new VentureNumber(boost::python::extract<double>(d["value"]))); }
  else if (type == "symbol") { return shared_ptr<VentureSymbol>(new VentureSymbol(boost::python::extract<string>(d["value"]))); }
  else if (type == "atom") { return shared_ptr<VentureAtom>(new VentureAtom(boost::python::extract<uint32_t>(d["value"]))); }
  else if (type == "simplex") { return parseSimplex(d); }
  else if (type == "array" || type == "list") {return parseArray(d); }
  else { throw "Unknown type '" + type + "'"; }
}

VentureValuePtr parseExpression(boost::python::object o)
{
  boost::python::extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return shared_ptr<VentureValue>(parseValue(getDict())); }
  
  boost::python::extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
  
  vector<VentureValuePtr> exp;
  
  boost::python::ssize_t L = boost::python::len(l);
  
  for(boost::python::ssize_t i=0; i<L; ++i)
  {
    exp.push_back(parseExpression(l[i]));
  }
  return shared_ptr<VentureValue>(new VentureArray(exp));
}
