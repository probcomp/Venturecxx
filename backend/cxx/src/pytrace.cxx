#include "value.h"
#include "env.h"
#include "node.h"
#include "pytrace.h"
#include "gkernel.h"
#include "infer.h"
#include "exp.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>

#include <iostream>

using boost::python::extract;

PyTrace::PyTrace(): Trace(), mcmc(new OutermostMixMH(this,new ScaffoldMHGKernelMaker(this))) {}

PyTrace::~PyTrace()
{
  OutermostMixMH * mkernel = dynamic_cast<OutermostMixMH*>(mcmc);
  ScaffoldMHGKernelMaker * gmaker = dynamic_cast<ScaffoldMHGKernelMaker*>(mkernel->gKernelMaker);
  delete gmaker;
  delete mkernel;
}

Expression PyTrace::parseExpression(boost::python::object o)
{
 boost::python::object pyClassObject = o.attr("__class__").attr("__name__");
 extract<string> p(pyClassObject);
 assert(p.check());
 string pyClass = p();

 if (pyClass == "str")
 {
   extract<string> s(o);
   return Expression(s());
 }
 else if (pyClass == "bool")
 {
   extract<bool> b(o);
   return Expression(new VentureBool(b()));
 }
 else if (pyClass == "int")
 {
   extract<int> n(o);
//   assert(n() >= 0); // may not fly
   return Expression(new VentureCount(n()));
 }

 else if (pyClass ==  "float")
 {
   extract<double> d(o);
   return Expression(new VentureDouble(d()));
 }

 vector<Expression> exps;
 boost::python::ssize_t L = boost::python::len(o);
 for(boost::python::ssize_t i=0;i<L;i++) {
   exps.push_back(parseExpression(o[i]));
 }
 return Expression(exps);
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  Expression exp = parseExpression(o);

  pair<double,Node*> p = evalVentureFamily(directiveID,exp);
  ventureFamilies.insert({directiveID,p.second});
}

boost::python::object PyTrace::extractPythonValue(size_t directiveID)
{
  Node * node = ventureFamilies[directiveID];
  assert(node);
  VentureValue * value = node->getValue();
  assert(value);
  return value->toPython();
}

void PyTrace::bindInGlobalEnv(string sym, size_t directiveID)
{
  globalEnvNode->getEnvironment()->addBinding(sym,ventureFamilies[directiveID]);
}

void PyTrace::observe(size_t directiveID,boost::python::object valueExp)
{
  Node * node = ventureFamilies[directiveID];
  Expression exp = parseExpression(valueExp);
  assert(exp.expType == ExpType::VALUE);
  node->observedValue = exp.value;
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

