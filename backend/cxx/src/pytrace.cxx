#include "value.h"
#include "node.h"
#include "env.h"
#include "pytrace.h"
#include "infer/gkernel.h"
#include "infer/mh.h"
#include "infer/gibbs.h"
#include "value.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>

#include <iostream>
#include <list>

using boost::python::extract;

PyTrace::PyTrace(): 
  Trace(), 
//  mcmc(new OutermostMixMH(this, new ScaffoldMHGKernel(this))) {}
  mcmc(new OutermostMixMH(this,new GibbsGKernel(this))) {}

PyTrace::~PyTrace()
{
  OutermostMixMH * mKernel = dynamic_cast<OutermostMixMH*>(mcmc);
  delete mKernel->gKernel;
  delete mcmc;
}

VentureValue * PyTrace::parseExpression(boost::python::object o)
{
 boost::python::object pyClassObject = o.attr("__class__").attr("__name__");
 extract<string> p(pyClassObject);
 assert(p.check());
 string pyClass = p();

 if (pyClass == "str")
 {
   extract<string> s(o);
   return new VentureSymbol(s());
 }
 else if (pyClass == "bool")
 {
   extract<bool> b(o);
   return new VentureBool(b());
 }
 else if (pyClass == "int")
 {
   extract<int> n(o);
   assert(n() >= 0);
   return new VentureCount(n());
 }

 else if (pyClass ==  "float")
 {
   extract<double> d(o);
   return new VentureDouble(d());
 }


 VentureList * exp = new VentureNil;
 
 boost::python::ssize_t L = boost::python::len(o);

 for(boost::python::ssize_t i=L;i > 0;i--) 
 {
   exp = new VenturePair(parseExpression(o[i-1]),exp);
 }
 return exp;
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  VentureValue * exp = parseExpression(o);

  pair<double,Node*> p = evalVentureFamily(directiveID,static_cast<VentureList*>(exp));
  ventureFamilies.insert({directiveID,{p.second,exp}});
}

boost::python::object PyTrace::extractPythonValue(size_t directiveID)
{
  Node * node;
  tie(node,ignore) = ventureFamilies[directiveID];
  assert(node);
  VentureValue * value = node->getValue();
  assert(value);
  return value->toPython();
}

void PyTrace::bindInGlobalEnv(string sym, size_t directiveID)
{
  globalEnv->addBinding(new VentureSymbol(sym),ventureFamilies[directiveID].first);
}

void PyTrace::observe(size_t directiveID,boost::python::object valueExp)
{
  Node * node;
  tie(node,ignore) = ventureFamilies[directiveID];
  VentureValue * val = parseExpression(valueExp);
  assert(!dynamic_cast<VenturePair*>(val));
  assert(!dynamic_cast<VentureSymbol*>(val));
  node->observedValue = val;
  constrain(node,true);
}

void PyTrace::infer(size_t n) { mcmc->infer(n); }

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("observe", &PyTrace::observe)
    .def("infer", &PyTrace::infer)
    ;
};

