#include "pysp.h"
#include "node.h"
#include "value.h"
#include "pyutils.h"

#include <boost/python.hpp>

PySP::~PySP()
{
}

VentureValue * PySP::simulateOutput(Node * node, gsl_rng * rng) const
{ 
  //  std::cout << "pysp calling simulateoutput" << std::endl;

  boost::python::list args;
  for (Node * operandNode : node->operandNodes)
  {
    args.append(operandNode->getValue()->toPython());
  }
  boost::python::object val = simulateOutputPython(args);
  boost::python::extract<boost::python::dict> getDict(val);
  assert(getDict.check());
  VentureValue * value = parseValue(getDict());
  assert(value);
  return value;
}

double PySP::logDensityOutput(VentureValue *val, Node *node) const
{
  //  std::cout << "calling logdensity" << std::endl;
  boost::python::list args;
  for (Node * operandNode : node->operandNodes)
    {
      // FIXME vkm/lovell decide on how to wrap sps such that python can call them; think through implications at all trace boundaries of a callable toPython()
      args.append(operandNode->getValue()->toPython());
    }
  //FIXME vkm/lovell improve type signature and checking if a non-double is returned (or at least test it!)
  //FIXME vkm/lovell think carefully about memory management and restrictions on saving values coming from venture
  return logDensityOutputPython(args, val->toPython());
}

boost::python::object PySP::simulateOutputPython(boost::python::list args) const
{
  return this->get_override("pysp_output_simulate")(args);
}

double PySP::logDensityOutputPython(boost::python::list args, boost::python::object value) const
{
  return this->get_override("pysp_output_logdensity")(args, value);
}

//FIXME: Remove the extra layer of classes here, and fix the exports to be more sensible
//FIXME: right now the name is coming from string constants in this source file
BOOST_PYTHON_MODULE(libsp)
{
  using namespace boost::python;
  class_<PySP, boost::noncopyable>("SP",init<>())
    //    .def("simulate", &PySP::simulateOutputPython)
    //    .def("logDensity", &PySP::logDensityOutputPython)
    ;
};
