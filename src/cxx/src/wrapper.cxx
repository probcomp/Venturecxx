#include "trace.h"
#include <boost/python.hpp>
#include <boost/python/object.hpp>

#include <iostream>

using boost::python::extract;

Expression Trace::parseExpression(boost::python::object o)
{
 extract<bool> b(o);
 extract<double> x(o);
 extract<std::string> s(o);

 boost::python::object pyClassObject = o.attr("__class__").attr("__name__");
 extract<std::string> p(pyClassObject);
 assert(p.check());
 std::string pyClass = p();

 if (pyClass == "str")
 {
   extract<std::string> s(o);
   return Expression(s());
 }
 else if (pyClass == "bool")
 {
   extract<bool> b(o);
   return Expression(new VentureBool(b));
 }
 else if (pyClass == "int")
 {
   extract<int> n(o);
   assert(n >= 0);
   return Expression(new VentureCount(n));
 }
 else if (pyClass ==  "float")
 {
   extract<double> d(o);
   return Expression(new VentureDouble(d));
 }

 std::vector<Expression> exps;
 boost::python::ssize_t L = boost::python::len(o);
 for(boost::python::ssize_t i=0;i<L;i++) {
   exps.push_back(parseExpression(o[i]));
 }
 return Expression(exps);
}

void Trace::evalExpression(std::string addressName, boost::python::object o)
{
  Address a(addressName);
  Expression exp = parseExpression(o);
  Environment globalEnv(Address::globalEnvironmentAddress);
  Scaffold scaffold;
  bool sr{false};
  OmegaDB omegaDB;

  evalFamily(a,exp,globalEnv,&scaffold,sr,omegaDB);
}

double Trace::getDouble(std::string addressName)
{
  VentureValue * value = _map[Address(addressName)]->getValue();
  VentureDouble * d = dynamic_cast<VentureDouble *>(value);
  assert(d);
  return d->x;
}

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<Trace>("Trace",init<>())
    .def("evalExpression", &Trace::evalExpression)
    .def("getDouble", &Trace::getDouble)
    ;
};
