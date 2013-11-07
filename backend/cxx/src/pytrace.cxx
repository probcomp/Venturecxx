#include "value.h"
#include "node.h"
#include "sp.h"
#include "scaffold.h"
#include "env.h"
#include "pytrace.h"
#include "infer/gkernel.h"
#include "infer/mh.h"
#include "infer/gibbs.h"
#include "infer/pgibbs.h"
#include "infer/meanfield.h"
#include "value.h"

#include "pyutils.h"
#include "file_utils.h"
#include <gsl/gsl_rng.h>

#include <iostream>
#include <list>
#include <map>

PyTrace::PyTrace(): 
  Trace(), 
  gkernels{
    {"mh", new ScaffoldMHGKernel(this)},
    {"gibbs", new GibbsGKernel(this)},
    {"pgibbs", new PGibbsGKernel(this)},
    {"meanfield",new MeanFieldGKernel(this)}}
{

  std::string module_str = "venture.pysps";
  boost::python::object module_namespace = boost::python::import(boost::python::str(module_str));
  boost::python::object module_path = module_namespace.attr("__path__")[0];
  std::string module_path_str = boost::python::extract<std::string>(module_path);
  // std::vector<std::string> dir_contents = lsdir("./pysps/");
  std::vector<std::string> dir_contents = lsdir(module_path_str);
  std::vector<std::string> pysp_files = filter_for_suffix(dir_contents, ".py");
  // print_string_v(pysp_files);

  if (pysp_files.begin() == pysp_files.end()) {
    std::cout << "No python sps to load" << std::endl;
  }

  for(std::vector<std::string>::const_iterator it=pysp_files.begin();
		  it!=pysp_files.end();
		  it++) {
    
	  std::string pysp_name = *it;
	  if(pysp_name == "__init__") continue;

	  bindPySP(module_str, pysp_name);
  }

}

void PyTrace::bindPySP(std::string module_str, std::string pysp_name)
{
	  std::cout << "trying to import " << pysp_name << std::endl;
	  std::string pysp_import_str = module_str + "." + pysp_name;
	  boost::python::object pysp_namespace = boost::python::import(boost::python::str(pysp_import_str));
	  std::cout << "boost::python::import'ed " << pysp_name << std::endl;

	  // get the function called "makeSP", and the funcion called "getSymbol" in the model
	  boost::python::object pysp = boost::python::getattr(pysp_namespace, "makeSP");
	  boost::python::object pysym = boost::python::getattr(pysp_namespace, "getSymbol");

	  // extract them
	  assert(!pysp.is_none());
	  my_sp_v.push_back(pysp());
	  boost::python::extract<SP*> spex(*my_sp_v.back());
	  
	  assert(!pysym.is_none());
	  my_sp_sym_v.push_back(pysym());
	  boost::python::extract<string> symex(*my_sp_sym_v.back());

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

	  std::cout << "added binding for new SP: " << sym << std::endl;
}

PyTrace::~PyTrace()
{
  for (pair<string,GKernel *> p : gkernels)
  {
    delete p.second;
  }
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  VentureValue * exp = parseExpression(o);

  pair<double,Node*> p = evalVentureFamily(directiveID,static_cast<VentureList*>(exp),nullptr);
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

void PyTrace::infer(boost::python::dict options) 
{ 
  string kernel = boost::python::extract<string>(options["kernel"]);
  size_t numTransitions = boost::python::extract<size_t>(options["transitions"]);
  bool useGlobalScaffold = boost::python::extract<bool>(options["use_global_scaffold"]);

  GKernel * gkernel = gkernels[kernel];

  if (useGlobalScaffold)
  {
    // TODO temporary -- gibbs checks the principal node for enumeration

    assert(kernel == "pgibbs");
    set<Node *> allNodes(randomChoices.begin(),randomChoices.end());
    gkernel->loadParameters(new ScaffoldMHParam(new Scaffold(allNodes),nullptr));
    gkernel->infer(numTransitions);
  }
  else
  {
    OutermostMixMH * outermostKernel = new OutermostMixMH(this,gkernel);
    outermostKernel->infer(numTransitions);
    delete outermostKernel;
  }
}

void PyTrace::set_seed(size_t n) {
  gsl_rng_set(rng, n);
}

size_t PyTrace::get_seed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("observe", &PyTrace::observe)
    .def("infer", &PyTrace::infer)
    .def("set_seed", &PyTrace::set_seed)
    .def("get_seed", &PyTrace::get_seed)
    ;
};

