// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

#include "pytrace.h"
#include "regen.h"
#include "scaffold.h"
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
#include "gkernels/rejection.h"
#include "gkernels/func_mh.h"
#include "gkernels/pgibbs.h"
#include "gkernels/egibbs.h"
#include "gkernels/slice.h"

#include <boost/foreach.hpp>

#include <boost/python/exception_translator.hpp>

PyTrace::PyTrace() : trace(new ConcreteTrace())
{
  trace->initialize();
}
PyTrace::~PyTrace() {}

void PyTrace::evalExpression(DirectiveID did, boost::python::object object)
{
  VentureValuePtr exp = parseExpression(object);
  pair<double,Node*> p = evalFamily(trace.get(),
                                    exp,
                                    trace->globalEnvironment,
                                    boost::shared_ptr<Scaffold>(new Scaffold()),
                                    false,
                                    boost::shared_ptr<DB>(new DB()),
                                    boost::shared_ptr<map<Node*,Gradient> >());
  assert(p.first == 0);
  assert(!trace->families.count(did));
  trace->families[did] = boost::shared_ptr<Node>(p.second);
}

void PyTrace::unevalDirectiveID(DirectiveID did)
{
 assert(trace->families.count(did));
 unevalFamily(trace.get(),trace->families[did].get(),boost::shared_ptr<Scaffold>(new Scaffold()),boost::shared_ptr<DB>(new DB()));
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
  OutputNode * appNode = trace->getConstrainableNode(node);
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

void PyTrace::unbindInGlobalEnv(const string& sym)
{
  trace->globalEnvironment->removeBinding(sym);
}

bool PyTrace::boundInGlobalEnv(const string& sym)
{
  return trace->globalEnvironment->safeLookupSymbol(sym) != NULL;
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
  // TODO This algorithm is totally wrong: https://app.asana.com/0/16653194948424/20100308871203
  double ls = 0.0;
  for (set<Node*>::iterator iter = trace->unconstrainedChoices.begin();
       iter != trace->unconstrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    boost::shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    boost::shared_ptr<Args> args = trace->getArgs(node);
    if (psp->canAbsorb(trace.get(), node, NULL))
    {
      ls += psp->logDensity(trace->getGroundValue(node),args);
    }
  }
  for (set<Node*>::iterator iter = trace->constrainedChoices.begin();
       iter != trace->constrainedChoices.end();
       ++iter)
  {
    ApplicationNode * node = dynamic_cast<ApplicationNode*>(*iter);
    boost::shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
    boost::shared_ptr<Args> args = trace->getArgs(node);
    ls += psp->logDensity(trace->getGroundValue(node),args);
  }
  return ls;
}

uint32_t PyTrace::numUnconstrainedChoices() { return trace->numUnconstrainedChoices(); }

// parses params and does inference
struct Inferer
{
  boost::shared_ptr<ConcreteTrace> trace;
  boost::shared_ptr<GKernel> gKernel;
  ScopeID scope;
  BlockID block;
  boost::shared_ptr<ScaffoldIndexer> scaffoldIndexer;
  size_t transitions;
  vector<boost::shared_ptr<Inferer> > subkernels;

  Inferer(boost::shared_ptr<ConcreteTrace> trace, boost::python::dict params) : trace(trace)
  {
    string kernel = boost::python::extract<string>(params["kernel"]);
    if (kernel == "mh")
    {
      gKernel = boost::shared_ptr<GKernel>(new MHGKernel);
    }
    else if (kernel == "bogo_possibilize")
    {
      gKernel = boost::shared_ptr<GKernel>(new BogoPossibilizeGKernel);
    }
    else if (kernel == "func_mh")
    {
      gKernel = boost::shared_ptr<GKernel>(new FuncMHGKernel);
    }
    else if (kernel == "pgibbs")
    {
      size_t particles = boost::python::extract<size_t>(params["particles"]);
      bool inParallel  = boost::python::extract<bool>(params["in_parallel"]);
      gKernel = boost::shared_ptr<GKernel>(new PGibbsGKernel(particles,inParallel));
    }
    else if (kernel == "gibbs")
    {
      bool inParallel  = boost::python::extract<bool>(params["in_parallel"]);
      gKernel = boost::shared_ptr<GKernel>(new EnumerativeGibbsGKernel(inParallel));
    }
    else if (kernel == "emap")
    {
      bool inParallel  = boost::python::extract<bool>(params["in_parallel"]);
      gKernel = boost::shared_ptr<GKernel>(new EnumerativeMAPGKernel(inParallel));
    }
    else if (kernel == "slice")
    {
      double w = boost::python::extract<double>(params["w"]);
      int m = boost::python::extract<int>(params["m"]);
      gKernel = boost::shared_ptr<GKernel>(new SliceGKernel(w,m));
    }
    else
    {
      cout << "\n***Kernel '" << kernel << "' not supported. Using MH instead.***" << endl;
      gKernel = boost::shared_ptr<GKernel>(new MHGKernel);
    }

    scope = fromPython(params["scope"]);
    block = fromPython(params["block"]);

    if (block->hasSymbol() && block->getSymbol() == "ordered_range")
    {
      VentureValuePtr minBlock = fromPython(params["min_block"]);
      VentureValuePtr maxBlock = fromPython(params["max_block"]);
      scaffoldIndexer = boost::shared_ptr<ScaffoldIndexer>(new ScaffoldIndexer(scope,block,minBlock,maxBlock));
    }
    else
    {
      scaffoldIndexer = boost::shared_ptr<ScaffoldIndexer>(new ScaffoldIndexer(scope,block));
    }
    transitions = boost::python::extract<size_t>(params["transitions"]);
  }

  void infer()
  {
    if (trace->numUnconstrainedChoices() == 0) { return; }
    for (size_t i = 0; i < transitions; ++i)
    {
      inferPrimitive(); inferAEKernels();
    }
  }

  void inferPrimitive()
  {
    mixMH(trace.get(), scaffoldIndexer, gKernel);
  }

  void inferAEKernels()
  {
    for (set<Node*>::iterator iter = trace->arbitraryErgodicKernels.begin();
      iter != trace->arbitraryErgodicKernels.end();
      ++iter)
    {
      OutputNode * node = dynamic_cast<OutputNode*>(*iter);
      assert(node);
      trace->getMadeSP(node)->AEInfer(trace->getMadeSPAux(node),trace->getArgs(node),trace->getRNG());
    }
  }
};

void PyTrace::primitive_infer(boost::python::dict params)
{
  Inferer inferer(trace, params);
  inferer.infer();
}

void translateStringException(const string& err) {
  PyErr_SetString(PyExc_RuntimeError, err.c_str());
}

void translateCStringException(const char* err) {
  PyErr_SetString(PyExc_RuntimeError, err);
}

double PyTrace::makeConsistent()
{
  return trace->makeConsistent();
}

void PyTrace::registerConstraints()
{
  trace->registerConstraints();
}

double PyTrace::logLikelihoodAt(boost::python::object pyscope, boost::python::object pyblock) {
  ScopeID scope = fromPython(pyscope);
  ScopeID block = fromPython(pyblock);
  return trace->logLikelihoodAt(scope, block);
}

double PyTrace::logJointAt(boost::python::object pyscope, boost::python::object pyblock) {
  ScopeID scope = fromPython(pyscope);
  ScopeID block = fromPython(pyblock);
  return trace->logJointAt(scope, block);
}

double PyTrace::likelihoodWeight()
{
  return trace->likelihoodWeight();
}

int PyTrace::numNodesInBlock(boost::python::object scope, boost::python::object block)
{
  return trace->getNodesInBlock(fromPython(scope), fromPython(block)).size();
}

boost::python::list PyTrace::numFamilies()
{
  boost::python::list xs;
  xs.append(trace->families.size());
  for (map<Node*, boost::shared_ptr<VentureSPRecord> >::iterator iter = trace->madeSPRecords.begin();
       iter != trace->madeSPRecords.end();
       ++iter)
    {
      if (iter->second->spFamilies->families.size()) { xs.append(iter->second->spFamilies->families.size()); }
    }
  return xs;
}

void PyTrace::freeze(DirectiveID did)
{
  trace->freezeDirectiveID(did);
}

boost::python::list PyTrace::scope_keys()
{
  boost::python::list xs;
  typedef pair<VentureValuePtr, SamplableMap<set<Node*> > > goal;
  BOOST_FOREACH(goal p, trace->scopes)
    {
      xs.append(p.first->toPython(trace.get())["value"]);
    }
  return xs;
}

void PyTrace::bindPumaSP(const string& sym, SP* sp)
{
  Node* node = trace->bindPrimitiveSP(sym, sp);
  trace->boundForeignSPNodes.insert(boost::shared_ptr<Node>(node));
}

BOOST_PYTHON_MODULE(libpumatrace)
{
  using namespace boost::python;

  boost::python::numeric::array::set_module_and_type("numpy", "ndarray");

  register_exception_translator<string>(&translateStringException);
  register_exception_translator<const char*>(&translateCStringException);

  class_<SP, SP* >("PumaSP", no_init); // raw pointer because Puma wants to take ownership
  class_<OrderedDB, boost::shared_ptr<OrderedDB> >("OrderedDB", no_init);

  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("unbindInGlobalEnv", &PyTrace::unbindInGlobalEnv)
    .def("boundInGlobalEnv", &PyTrace::boundInGlobalEnv)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindPythonSP", &PyTrace::bindPythonSP)
    .def("bindPumaSP", &PyTrace::bindPumaSP)
    .def("set_seed", &PyTrace::setSeed)
    .def("get_seed", &PyTrace::getSeed)
    .def("numRandomChoices", &PyTrace::numUnconstrainedChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("primitive_infer", &PyTrace::primitive_infer)
    .def("makeConsistent", &PyTrace::makeConsistent)
    .def("registerConstraints", &PyTrace::registerConstraints)
    .def("log_likelihood_at", &PyTrace::logLikelihoodAt)
    .def("log_joint_at", &PyTrace::logJointAt)
    .def("likelihood_weight", &PyTrace::likelihoodWeight)
    .def("numNodesInBlock", &PyTrace::numNodesInBlock)
    .def("numFamilies", &PyTrace::numFamilies)
    .def("freeze", &PyTrace::freeze)
    .def("stop_and_copy", &PyTrace::stop_and_copy, return_value_policy<manage_new_object>())
    .def("makeSerializationDB", &PyTrace::makeEmptySerializationDB)
    .def("makeSerializationDB", &PyTrace::makeSerializationDB)
    .def("dumpSerializationDB", &PyTrace::dumpSerializationDB)
    .def("unevalAndExtract", &PyTrace::unevalAndExtract)
    .def("restore", &PyTrace::restoreDirectiveID)
    .def("evalAndRestore", &PyTrace::evalAndRestore)
    .def("scope_keys", &PyTrace::scope_keys)
    ;
};
