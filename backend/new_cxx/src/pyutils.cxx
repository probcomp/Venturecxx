#include "pyutils.h"
#include "values.h"

#include <iostream>

using std::cout;
using std::endl;

VentureValuePtr parseValue(boost::python::dict d)
{
  if (d["type"] == "boolean") { return shared_ptr<VentureBool>(new VentureBool(boost::python::extract<bool>(d["value"]))); }
  else if (d["type"] == "number") { return shared_ptr<VentureNumber>(new VentureNumber(boost::python::extract<double>(d["value"]))); }
  else if (d["type"] == "symbol") { return shared_ptr<VentureSymbol>(new VentureSymbol(boost::python::extract<string>(d["value"]))); }
  else if (d["type"] == "atom") { return shared_ptr<VentureAtom>(new VentureAtom(boost::python::extract<uint32_t>(d["value"]))); }
  else { assert(false); }
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
  
  for(boost::python::ssize_t i=0; i<L; i++)
  {
exp.push_back(parseExpression(l[i]));
  }
  return shared_ptr<VentureValue>(new VentureArray(exp));
}
