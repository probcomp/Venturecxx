#include "value.h"
#include "node.h"
#include "sp.h"
#include "env.h"
#include "pytrace.h"
#include "infer/gkernel.h"
#include "infer/mh.h"
#include "infer/gibbs.h"
#include "value.h"
#include "pyutils.h"

#include <iostream>
#include <list>



PyTrace::PyTrace(): 
  Trace(), 
//  mcmc(new OutermostMixMH(this, new ScaffoldMHGKernel(this))) {}
  mcmc(new OutermostMixMH(this,new GibbsGKernel(this)))
{

  // TODO LOVELL 
  // get a list of all files 
  // iterate over the FILES in inc/pysps, and for each file
  // do the following, as in the code below:


// FOR each file in inc/pysps, import the module in the file

  // "square" will become "whatever-the-filename-is"
  boost::python::object pysp_namespace = boost::python::import("square");

  // get the function called "makeSP", and the funcion called "getSymbol" in the model
  boost::python::object pysp = boost::python::getattr(pysp_namespace, "makeSP");
  boost::python::object pysym = boost::python::getattr(pysp_namespace, "getSymbol");


  // extract them
  assert(!pysp.is_none());
  boost::python::extract<SP*> spex(pysp());

  assert(!pysym.is_none());
  boost::python::extract<string> symex(pysym());

  assert(spex.check());
  assert(symex.check());

  SP * sp = spex();
  string sym = symex();

  assert(!sp->makesESRs);
  assert(!sp->makesHSRs);
  
  // create a node for the sp value
  Node * spNode = new Node(NodeType::VALUE);
  // set the value
  spNode->setValue(new VentureSP(sp));
  // do some crucial bookkeeping
  processMadeSP(spNode,false);
  // add the binding
  primitivesEnv->addBinding(new VentureSymbol(sym),spNode);

// END for loop

}


PyTrace::~PyTrace()
{
  OutermostMixMH * mKernel = dynamic_cast<OutermostMixMH*>(mcmc);
  delete mKernel->gKernel;
  delete mcmc;
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

