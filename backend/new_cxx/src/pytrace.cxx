#include "pytrace.h"
#include "regen.h"
#include "detach.h"
#include "concrete_trace.h"
#include "db.h"
#include "env.h"
#include "values.h"
#include "sp.h"
#include "mixmh.h"
#include "indexer.h"
#include "gkernel.h"
#include "gkernels/mh.h"
#include "gkernels/func_mh.h"
#include "gkernels/pgibbs.h"
#include "gkernels/egibbs.h"
#include "gkernels/slice.h"
#include "gkernels/map.h"
#include "gkernels/hmc.h"

#include <boost/python/exception_translator.hpp>

PyTrace::PyTrace() : trace(new ConcreteTrace()), continuous_inference_running(false) {}
PyTrace::~PyTrace() {}

void PyTrace::evalExpression(DirectiveID did, boost::python::object object) 
{
  cout << "1" << endl;
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
  cout << "2" << endl;
}

void PyTrace::unevalDirectiveID(DirectiveID did) 
{ 
 assert(trace->families.count(did));
 unevalFamily(trace.get(),trace->families[did].get(),shared_ptr<Scaffold>(new Scaffold()),shared_ptr<DB>(new DB()));
 trace->families.erase(did);
}

void PyTrace::observe(DirectiveID did,boost::python::object valueExp)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  trace->unpropagatedObservations[root.get()] = parseExpression(valueExp);
}

void PyTrace::unobserve(DirectiveID did)
{
  assert(trace->families.count(did));
  Node * node = trace->families[did].get();
  OutputNode * appNode = trace->getOutermostNonRefAppNode(node);
  if (trace->isObservation(node)) { unconstrain(trace.get(),appNode); trace->unobserveNode(node); }
  else
  {
    assert(trace->unpropagatedObservations.count(node));
    trace->unpropagatedObservations.erase(node);
  }
}

void PyTrace::bindInGlobalEnv(const string& sym, DirectiveID did)
{
  trace->globalEnvironment->addBinding(sym,trace->families[did].get());
}

boost::python::object PyTrace::extractPythonValue(DirectiveID did)
{
  assert(trace->families.count(did));
  RootOfFamily root = trace->families[did];
  VentureValuePtr value = trace->getValue(root.get());
  assert(value.get());
  return value->toPython(trace.get());
}

void PyTrace::setSeed(size_t n) {
  gsl_rng_set(trace->getRNG(), n);
}

size_t PyTrace::getSeed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


double PyTrace::getGlobalLogScore() 
{
  double ls = 0.0;
  for (set<Node*>::iterator iter = trace->unconstrainedChoices.begin();
       iter != trace->unconstrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    shared_ptr<Args> args = trace->getArgs(node);
    ls += psp->logDensity(trace->getValue(node),args);
  }
  for (set<Node*>::iterator iter = trace->constrainedChoices.begin();
       iter != trace->constrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    shared_ptr<Args> args = trace->getArgs(node);
    ls += psp->logDensity(trace->getValue(node),args);
  }
  return ls;
}

uint32_t PyTrace::numUnconstrainedChoices() { return trace->numUnconstrainedChoices(); }

VentureValuePtr getParam(const string& name, const boost::python::dict& params)
{
  boost::python::extract<string> getSymbol(params[name]);
  boost::python::extract<int> getInt(params[name]);
  boost::python::extract<double> getDouble(params[name]);
  boost::python::extract<bool> getBool(params[name]);
  if (getSymbol.check()) { return VentureValuePtr(new VentureSymbol(getSymbol())); }
  else if (getInt.check()) { return VentureValuePtr(new VentureNumber(getInt())); }
  else if (getDouble.check()) { return VentureValuePtr(new VentureNumber(getDouble())); }
  else if (getBool.check()) { return VentureValuePtr(new VentureBool(getBool())); }
  throw "Invalid parameter '" + name + "' in infer instruction.";
}

// parses params and does inference
struct Inferer
{
  shared_ptr<ConcreteTrace> trace;
  shared_ptr<GKernel> gKernel;
  ScopeID scope;
  BlockID block;
  shared_ptr<ScaffoldIndexer> scaffoldIndexer;
  size_t transitions;
  
  Inferer(shared_ptr<ConcreteTrace> trace, boost::python::dict params) : trace(trace)
  {
    string kernel = boost::python::extract<string>(params["kernel"]);
    if (kernel == "mh")
    {
      gKernel = shared_ptr<GKernel>(new MHGKernel);
    }
    else if (kernel == "func_mh")
    {
      gKernel = shared_ptr<GKernel>(new FuncMHGKernel);
    }
    else if (kernel == "pgibbs")
    {
      size_t particles = boost::python::extract<size_t>(params["particles"]);
      gKernel = shared_ptr<GKernel>(new PGibbsGKernel(particles));
    }
    else if (kernel == "gibbs")
    {
      gKernel = shared_ptr<GKernel>(new EnumerativeGibbsGKernel);
    }
    else if (kernel == "slice")
    {
      gKernel = shared_ptr<GKernel>(new SliceGKernel);
    }
    else if (kernel == "map" || kernel == "hmc")  
    {
      double epsilon = 0.02;
      if(params.has_key("rate")) {
        epsilon = boost::python::extract<double>(params["rate"]);
      }
      double steps = 3;
      if(params.has_key("steps")) {
        steps = boost::python::extract<double>(params["steps"]);
      }
      if(kernel == "map")
        gKernel = shared_ptr<GKernel>(new MAPGKernel(epsilon, steps));
      else if(kernel == "hmc")
        gKernel = shared_ptr<GKernel>(new HMCGKernel(epsilon, steps));
    }
    else
    {
      cout << "\n***Kernel '" << kernel << "' not supported. Using MH instead.***" << endl;
      gKernel = shared_ptr<GKernel>(new MHGKernel);
    }
    
    scope = getParam("scope", params);
    block = getParam("block", params);
    scaffoldIndexer = shared_ptr<ScaffoldIndexer>(new ScaffoldIndexer(scope,block));
    
    transitions = boost::python::extract<size_t>(params["transitions"]);
  }
  
  void infer()
  {
    if (trace->numUnconstrainedChoices() == 0) { return; }
    
    for (size_t i = 0; i < transitions; ++i)
    {
      mixMH(trace.get(), scaffoldIndexer, gKernel);

      for (set<Node*>::iterator iter = trace->arbitraryErgodicKernels.begin();
        iter != trace->arbitraryErgodicKernels.end();
        ++iter)
      {
        OutputNode * node = dynamic_cast<OutputNode*>(*iter);
        assert(node);
        trace->getMadeSP(node)->AEInfer(trace->getMadeSPAux(node),trace->getArgs(node),trace->getRNG());
      }
    }
  }
};

// TODO URGENT placeholder
void PyTrace::infer(boost::python::dict params) 
{ 
  trace->makeConsistent();
  
  Inferer inferer(trace, params);
  inferer.infer();
}

boost::python::dict PyTrace::continuous_inference_status()
{
  boost::python::dict status;
  status["running"] = continuous_inference_running;
  if(continuous_inference_running) {
    status["params"] = continuous_inference_params;
  }
  return status;
}

void run_continuous_inference(shared_ptr<Inferer> inferer, bool * flag)
{
  while(*flag) { inferer->infer(); }
}

void PyTrace::start_continuous_inference(boost::python::dict params)
{
  stop_continuous_inference();
  
  continuous_inference_params = params;
  continuous_inference_running = true;
  shared_ptr<Inferer> inferer = shared_ptr<Inferer>(new Inferer(trace, params));
  
  trace->makeConsistent();
  
  continuous_inference_thread = new boost::thread(run_continuous_inference, inferer, &continuous_inference_running);
}

void PyTrace::stop_continuous_inference() {
  if(continuous_inference_running) {
    continuous_inference_running = false;
    continuous_inference_thread->join();
    delete continuous_inference_thread;
  }
}

void translateStringException(const string& err) {
  PyErr_SetString(PyExc_RuntimeError, err.c_str());
}

void translateCStringException(const char* err) {
  PyErr_SetString(PyExc_RuntimeError, err);
}

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  
  register_exception_translator<string>(&translateStringException);
  register_exception_translator<const char*>(&translateCStringException);

  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("set_seed", &PyTrace::setSeed)
    .def("get_seed", &PyTrace::getSeed)
    .def("numRandomChoices", &PyTrace::numUnconstrainedChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("infer", &PyTrace::infer)
    .def("continuous_inference_status", &PyTrace::continuous_inference_status)
    .def("start_continuous_inference", &PyTrace::start_continuous_inference)
    .def("stop_continuous_inference", &PyTrace::stop_continuous_inference)
    ;
};

