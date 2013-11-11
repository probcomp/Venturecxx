#include "value.h"
#include "node.h"
#include "sp.h"
#include "scaffold.h"
#include "flush.h"
#include "env.h"
#include "pytrace.h"
#include "infer/gkernel.h"
#include "infer/mh.h"
#include "infer/gibbs.h"
#include "infer/pgibbs.h"
#include "infer/meanfield.h"
#include "value.h"
#include "scaffold.h"

#include <gsl/gsl_rng.h>

#include <iostream>
#include <list>

PyTrace::PyTrace() :
  trace(new Trace()),
  gkernels{
    {{"mh",false}, new OutermostMixMH(trace,new ScaffoldMHGKernel(trace))},
    {{"mh",true}, new GlobalScaffoldMixMH(trace,new ScaffoldMHGKernel(trace))},

    {{"pgibbs",false}, new OutermostMixMH(trace,new PGibbsGKernel(trace))},
    {{"pgibbs",true}, new GlobalScaffoldMixMH(trace,new PGibbsGKernel(trace))},

    {{"gibbs",false}, new OutermostMixMH(trace,new GibbsGKernel(trace))},

    {{"meanfield",false}, new OutermostMixMH(trace,new MeanFieldGKernel(trace))},
    {{"meanfield",true}, new GlobalScaffoldMixMH(trace,new MeanFieldGKernel(trace))}}
 {}

PyTrace::~PyTrace()
{
  delete trace;
  for (pair< pair<string,bool>,MixMHKernel *> p : gkernels)
  {
    p.second->destroyChildGKernel();
    delete p.second;
  }
}

VentureValue * PyTrace::parseValue(boost::python::dict d)
{
  if (d["type"] == "boolean") { return new VentureBool(boost::python::extract<bool>(d["value"])); }
  else if (d["type"] == "number") { return new VentureNumber(boost::python::extract<double>(d["value"])); }
  else if (d["type"] == "symbol") { return new VentureSymbol(boost::python::extract<string>(d["value"])); }
  else if (d["type"] == "atom") { return new VentureAtom(boost::python::extract<uint32_t>(d["value"])); }
  else { assert(false); }
}


VentureValue * PyTrace::parseExpression(boost::python::object o)
{
  boost::python::extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return parseValue(getDict()); }
  
  boost::python::extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
  
  VentureList * exp = new VentureNil;
  
  boost::python::ssize_t L = boost::python::len(l);
  
  for(boost::python::ssize_t i=L;i > 0;i--) 
  {
    exp = new VenturePair(parseExpression(l[i-1]),exp);
  }
  return exp;
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  VentureValue * exp = parseExpression(o);
  pair<double,Node*> p = trace->evalVentureFamily(directiveID,static_cast<VentureList*>(exp),nullptr);
  assert(!trace->ventureFamilies.count(directiveID));
  trace->ventureFamilies.insert({directiveID,{p.second,exp}});

}

void PyTrace::unevalDirectiveID(size_t directiveID)
{
  OmegaDB * omegaDB = new OmegaDB;
  trace->detachVentureFamily(trace->ventureFamilies[directiveID].first,omegaDB);
  flushDB(omegaDB,false);
  trace->ventureFamilies.erase(directiveID);
}

boost::python::object PyTrace::extractPythonValue(size_t directiveID)
{
  Node * node;
  tie(node,ignore) = trace->ventureFamilies[directiveID];
  assert(node);
  VentureValue * value = node->getValue();
  assert(value);
  return value->toPython();
}

void PyTrace::bindInGlobalEnv(string sym, size_t directiveID)
{
  trace->globalEnv->addBinding(new VentureSymbol(sym),trace->ventureFamilies[directiveID].first);
}

void PyTrace::observe(size_t directiveID,boost::python::object valueExp)
{
  Node * node;
  tie(node,ignore) = trace->ventureFamilies[directiveID];
  VentureValue * val = parseExpression(valueExp);
  assert(!dynamic_cast<VenturePair*>(val));
  assert(!dynamic_cast<VentureSymbol*>(val));
  node->observedValue = val;
  trace->constrain(node,true);
}

double PyTrace::getGlobalLogScore()
{
  double ls = 0.0;
  for (Node * node : trace->randomChoices)
  {
    ls += node->sp()->logDensity(node->getValue(),node);
  }
  for (Node * node : trace->constrainedChoices)
  {
    ls += node->sp()->logDensity(node->getValue(), node);
  }
  return ls;
}

uint32_t PyTrace::numRandomChoices()
{
  return trace->numRandomChoices();
}

void PyTrace::unobserve(size_t directiveID)
{
  Node * root = trace->ventureFamilies[directiveID].first;
  trace->unconstrain(root,true);

}

void PyTrace::set_seed(size_t n) {
  gsl_rng_set(trace->rng, n);
}

size_t PyTrace::get_seed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


void PyTrace::infer(boost::python::dict params) 
{ 
  size_t numTransitions = boost::python::extract<size_t>(params["transitions"]);
  string kernel = boost::python::extract<string>(params["kernel"]);
  bool useGlobalScaffold = boost::python::extract<bool>(params["use_global_scaffold"]);
  
  assert(!(useGlobalScaffold && kernel == "gibbs"));
  MixMHKernel * gkernel = gkernels[make_pair(kernel,useGlobalScaffold)];
  gkernel->infer(numTransitions);
}

boost::python::dict PyTrace::continuous_inference_status() {
  boost::python::dict status;
  status["running"] = continuous_inference_running;
  if(continuous_inference_running) {
    status["params"] = continuous_inference_params;
  }
  return status;
}

void run_continuous_inference(MixMHKernel * gkernel, bool * flag) {
  while(*flag) {
    gkernel->infer(1);
  }
}

void PyTrace::start_continuous_inference(boost::python::dict params) {
  stop_continuous_inference();

  string kernel = boost::python::extract<string>(params["kernel"]);
  bool useGlobalScaffold = boost::python::extract<bool>(params["use_global_scaffold"]);
  assert(!(useGlobalScaffold && kernel == "gibbs"));
  MixMHKernel * gkernel = gkernels[make_pair(kernel,useGlobalScaffold)];

  continuous_inference_params = params;
  continuous_inference_running = true;
  continuous_inference_thread = new std::thread(run_continuous_inference, gkernel, &continuous_inference_running);
}

void PyTrace::stop_continuous_inference() {
  if(continuous_inference_running) {
    continuous_inference_running = false;
    continuous_inference_thread->join();
    delete continuous_inference_thread;
  }
}

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("numRandomChoices", &PyTrace::numRandomChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("infer", &PyTrace::infer)
    .def("set_seed", &PyTrace::set_seed)
    .def("get_seed", &PyTrace::get_seed)
    .def("continuous_inference_status", &PyTrace::continuous_inference_status)
    .def("start_continuous_inference", &PyTrace::start_continuous_inference)
    .def("stop_continuous_inference", &PyTrace::stop_continuous_inference)
    ;
};

