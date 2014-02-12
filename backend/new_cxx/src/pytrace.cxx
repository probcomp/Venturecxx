#include "pytrace.h"
#include "regen.h"
#include "concrete_trace.h"
#include "db.h"
#include "env.h"
#include "values.h"

PyTrace::PyTrace() : trace(shared_ptr<ConcreteTrace>(new ConcreteTrace())) {}
PyTrace::~PyTrace() {}
  
void PyTrace::evalExpression(DirectiveID did, boost::python::object object) 
{
  VentureValuePtr exp = parseExpression(object);
  pair<double,Node*> p = evalFamily(trace.get(),
				    exp,
				    trace->globalEnvironment,
				    shared_ptr<Scaffold>(new Scaffold()),
				    shared_ptr<DB>(new DB()),
				    shared_ptr<map<Node*,Gradient> >());
  assert(p.first == 0);
  assert(!trace->families.count(did));
  trace->families[did] = shared_ptr<Node>(p.second);
}

void PyTrace::unevalDirectiveID(DirectiveID did) 
{ 
  // assert(trace->families.count(did));
  // unevalFamily(trace.get(),trace->families[did],shared_ptr<Scaffold>(new Scaffold()),shared_ptr<DB>(new DB()));
  // trace->families.erase(did);
}

void PyTrace::observe(DirectiveID did,boost::python::object valueExp)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  trace->unpropagatedObservations[root.get()] = parseExpression(valueExp);
}

void PyTrace::unobserve(DirectiveID directiveID)
{
  // assert(trace->families.count(did));
  // Node * node = trace->families[id];
  // OutputNode * appNode = trace->getOutermostNonReferenceApplication(node);
  // if (trace->isObservation(node)) { unconstrain(trace.get(),appNode); }
  // else
  // {
  //   assert(trace->unpropagatedObservations.count(node));
  //   trace->unpropagatedObservations.erase(node);
  // }
}

void PyTrace::bindInGlobalEnv(string sym, DirectiveID did)
{
  trace->globalEnvironment->addBinding(shared_ptr<VentureSymbol>(new VentureSymbol(sym)),trace->families[did].get());
}

boost::python::object PyTrace::extractPythonValue(DirectiveID did)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  VentureValuePtr value = trace->getValue(root.get());
  assert(value.get());
  return value->toPython();
}

void PyTrace::setSeed(size_t n) {
  gsl_rng_set(trace->rng, n);
}

size_t PyTrace::getSeed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


double PyTrace::getGlobalLogScore() 
{
  // double ls = 0.0;
  // for (size_t i = 0; i < trace->unconstrainedRandomChoices.size(); ++i)
  // {
  //   Node * node = trace->unconstrainedRandomChoices[i];
  //   ls += trace->getPSP(node)->logDensity(trace->getValue(node),node);
  // }
  // for (size_t i = 0; i < trace->constrainedRandomChoices.size(); ++i)
  // {
  //   Node * node = trace->constrainedRandomChoices[i];
  //   ls += trace->getPSP(node)->logDensity(trace->getValue(node),node);
  // }
  // return ls;
  return 0;
}

uint32_t PyTrace::numUnconstrainedChoices() { return trace->numUnconstrainedChoices(); }

void PyTrace::infer(boost::python::dict params) { throw "INFER not yet implemented"; }

  
BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("extractPythonValue", &PyTrace::extractPythonValue)
    .def("set_seed", &PyTrace::setSeed)
    .def("get_seed", &PyTrace::getSeed)
    .def("numRandomChoices", &PyTrace::numUnconstrainedChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("infer", &PyTrace::infer)
    ;
};

