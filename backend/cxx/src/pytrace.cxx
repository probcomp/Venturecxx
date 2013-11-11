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

#include "pyutils.h"
#include "file_utils.h"
#include <gsl/gsl_rng.h>

#include <iostream>
#include <list>
#include <map>

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
{

  std::string module_str = "venture.pysps";
  boost::python::object module_namespace = boost::python::import(boost::python::str(module_str));
  boost::python::object module_path = module_namespace.attr("__path__")[0];
  std::string module_path_str = boost::python::extract<std::string>(module_path);
  // std::vector<std::string> dir_contents = lsdir("./pysps/");
  std::vector<std::string> dir_contents = lsdir(module_path_str);
  std::vector<std::string> pysp_files = filter_for_suffix(dir_contents, ".py");
  // print_string_v(pysp_files);

  for(std::vector<std::string>::const_iterator it=pysp_files.begin();
      it!=pysp_files.end();
      it++) {
    
    std::string pysp_name = *it;
    if(pysp_name == "__init__") continue;

    bindPySP(module_str, pysp_name);
  }

#  if (pysp_files.begin() == pysp_files.end()) {
#    std::cout << "No python sps to load" << std::endl;
#  } else {
#    std::cout << "Done loading python SPs" << std::endl;
#  }
}

PyTrace::~PyTrace()
{
  // Destroy the references we own to Python SPs, so that the
  // automatic machinery in python and boost handles the rest
  // correctly
  pysp_objects_vec.clear();
    
  delete trace;

  for (pair< pair<string,bool>,MixMHKernel *> p : gkernels)
  {
    p.second->destroyChildGKernel();
    delete p.second;
  }
}

void PyTrace::bindPySP(std::string module_str, std::string pysp_name)
{
  std::string pysp_import_str = module_str + "." + pysp_name;
  
  boost::python::object pysp_namespace = boost::python::import(boost::python::str(pysp_import_str));

  pysp_objects_vec.push_back(pysp_namespace);

  //  std::cout << "imported " << pysp_import_str << std::endl;

  //FIXME Error check this better

  //Get and apply the makeSP procedure
  boost::python::object pysp = boost::python::getattr(pysp_namespace, "makeSP");
  assert(!pysp.is_none());
  pysp_objects_vec.push_back(pysp());
  boost::python::extract<SP*> spex(*pysp_objects_vec.back());
  assert(spex.check());
  SP * sp = spex();

  //Get and apply the getSymbol procedure
  boost::python::object pysym = boost::python::getattr(pysp_namespace, "getSymbol");
  assert(!pysym.is_none());
  pysp_objects_vec.push_back(pysym());
  boost::python::extract<string> symex(*pysp_objects_vec.back());
  assert(symex.check());
  string sym = symex();  
  //  std::cout << "symbol: " << sym << std::endl;
  sp->name = sym;

  // get the value canAbsorb
  boost::python::object pycanabsorb = boost::python::getattr(pysp_namespace, "canAbsorb");
  pysp_objects_vec.push_back(pycanabsorb);
  boost::python::extract<bool> ex_canabsorb(pycanabsorb);
  bool canAbsorb = ex_canabsorb();
  sp->canAbsorbOutput = canAbsorb;
  //  std::cout << "can absorb: " << canAbsorb << std::endl;

  // get the value isRandom
  boost::python::object pyisrandom = boost::python::getattr(pysp_namespace, "isRandom");
  pysp_objects_vec.push_back(pyisrandom);
  boost::python::extract<bool> ex_israndom(pyisrandom);
  bool isRandom = ex_israndom();
  sp->isRandomOutput = isRandom;
  //  std::cout << "is random: " << isRandom << std::endl;

  // create a node for the sp value
  Node * spNode = new Node(NodeType::VALUE);
  VentureSP * vsp = new VentureSP(sp);
  vsp->sp_automatically_deleted = true;
  // set the value
  spNode->setValue(vsp);
  // do some crucial bookkeeping
  trace->processMadeSP(spNode,false);
  // add the binding
  trace->primitivesEnv->addBinding(new VentureSymbol(sym),spNode);
  
  //  std::cout << "added binding for new SP: " << sym << std::endl;
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  VentureValue * exp = parseExpression(o);

  pair<double,Node*> p = trace->evalVentureFamily(directiveID,static_cast<VentureList*>(exp),nullptr);
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
  std::cout << "pytrace getgloballogscore" << std::endl;

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
  trace->unconstrain(root);

  if (root->isReference())
  { root->sourceNode->ownsValue = true; }
  else
  { root->ownsValue = true; }

}

void PyTrace::set_seed(size_t n) {
  gsl_rng_set(trace->rng, n);
}

size_t PyTrace::get_seed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


void PyTrace::infer(boost::python::dict options) 
{ 
  size_t numTransitions = boost::python::extract<size_t>(options["transitions"]);
  string kernel = boost::python::extract<string>(options["kernel"]);
  bool useGlobalScaffold = boost::python::extract<bool>(options["use_global_scaffold"]);
  
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

