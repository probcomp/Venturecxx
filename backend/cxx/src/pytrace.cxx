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
#include "file_utils.h"

#include <iostream>
#include <list>
#include <map>


PyTrace::PyTrace(): 
  Trace(), 
//  mcmc(new OutermostMixMH(this, new ScaffoldMHGKernel(this))) {}
  mcmc(new OutermostMixMH(this,new GibbsGKernel(this)))
{

  std::vector<std::string> dir_contents = lsdir("/opt/Venturecxx/backend/cxx/inc/pysps/");
  std::vector<std::string> pysp_files = filter_for_suffix(dir_contents, ".py");
  // print_string_v(pysp_files);

  map<std::string, boost::python::object> string_to_pysp_namespace;
  for(std::vector<std::string>::const_iterator it=pysp_files.begin();
		  it!=pysp_files.end();
		  it++) {
	  std::string pysp_file = *it;
	  if(pysp_file == "__init__") continue;
	  string_to_pysp_namespace[pysp_file] = boost::python::import(boost::python::str(pysp_file));
	  // std::cout << "boost::python::import'ed " << pysp_file << std::endl;
  }

  std::string which_pysp = "square";
  boost::python::object pysp_namespace = string_to_pysp_namespace[which_pysp];

  // get the function called "makeSP", and the funcion called "getSymbol" in the model
  boost::python::object pysp = boost::python::getattr(pysp_namespace, "makeSP");
  boost::python::object pysym = boost::python::getattr(pysp_namespace, "getSymbol");


  // extract them
  assert(!pysp.is_none());
  my_sp = pysp();
  boost::python::extract<SP*> spex(my_sp);

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

