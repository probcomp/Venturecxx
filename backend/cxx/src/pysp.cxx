#include "pysp.h"
#include "node.h"
#include "value.h"
#include "pyutils.h"

#include <boost/python.hpp>

VentureValue * PySP::simulateOutput(Node * node, gsl_rng * rng) const
{ 
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

boost::python::object PySP::simulateOutputPython(boost::python::list args) const
{
  return this->get_override("simulate")(args);
}

BOOST_PYTHON_MODULE(libsp)
{
  using namespace boost::python;
  class_<PySP, boost::noncopyable>("SP",init<>())
    .def("simulate", &PySP::simulateOutputPython)
    ;
};
