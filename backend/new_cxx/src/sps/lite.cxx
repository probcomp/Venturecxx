#include "sps/lite.h"
#include "sprecord.h"
#include "pyutils.h"
#include "pytrace.h"
#include "concrete_trace.h"
#include "regen.h"
#include "env.h"

VentureValuePtr foreignFromPython(boost::python::object thing)
{
  // proxy for pyutils::parseValue that handles foreign SPs by wrapping them
  // TODO: should foreign_sp be a recognized stack dict type?
  if (thing["type"] == "foreign_sp")
  {
    boost::python::object sp = thing["value"];
    return VentureValuePtr(new VentureSPRecord(new ForeignLiteSP(sp),
                                               new ForeignLiteSPAux(sp)));
  }
  else
  {
    return parseValue(boost::python::extract<boost::python::dict>(thing));
  }
}

VentureValuePtr ForeignLitePSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux)->aux;
  boost::python::object foreignResult = psp.attr("simulate")(foreignOperandValues, foreignAux);
  return foreignFromPython(foreignResult);
}

double ForeignLitePSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux)->aux;
  boost::python::object foreignLogDensity = psp.attr("logDensity")(foreignValue, foreignOperandValues, foreignAux);
  return boost::python::extract<double>(foreignLogDensity);
}

void ForeignLitePSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux)->aux;
  psp.attr("incorporate")(foreignValue, foreignOperandValues, foreignAux);
}

void ForeignLitePSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux)->aux;
  psp.attr("unincorporate")(foreignValue, foreignOperandValues, foreignAux);
}

bool ForeignLitePSP::isRandom() const
{
  return boost::python::extract<bool>(psp.attr("isRandom")());
}

bool ForeignLitePSP::canAbsorb(ConcreteTrace * trace, ApplicationNode * appNode, Node * parentNode) const
{
  // TODO: include the node information somehow
  // currently the Lite wrapper stubs it
  return boost::python::extract<bool>(psp.attr("canAbsorb")());
}

bool ForeignLitePSP::childrenCanAAA() const
{
  return boost::python::extract<bool>(psp.attr("childrenCanAAA")());
}

bool ForeignLitePSP::canEnumerateValues(shared_ptr<Args> args) const
{
  // TODO: Lite SPs do not seem to implement this usefully.
  return true;
}

vector<VentureValuePtr> ForeignLitePSP::enumerateValues(shared_ptr<Args> args) const
{
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux)->aux;
  boost::python::object foreignResult = psp.attr("enumerateValues")(foreignOperandValues, foreignAux);
  boost::python::list foreignValues = boost::python::extract<boost::python::list>(foreignResult);
  vector<VentureValuePtr> values;
  for (boost::python::ssize_t i = 0; i < boost::python::len(foreignValues); ++i)
  {
    values.push_back(foreignFromPython(foreignValues[i]));
  }
  return values;
}

double ForeignLitePSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(spAux)->aux;
  boost::python::object foreignLogDensityOfCounts = psp.attr("logDensityOfCounts")(foreignAux);
  return boost::python::extract<double>(foreignLogDensityOfCounts);
}

boost::python::dict ForeignLiteSP::toPython(Trace * trace, shared_ptr<SPAux> aux) const
{
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(aux)->aux;
  // TODO: make this transparent if possible
  boost::python::dict stackDict;
  stackDict["type"] = "foreign_sp";
  stackDict["sp"] = sp;
  stackDict["value"] = sp.attr("show")(foreignAux);
  return stackDict;
}

void PyTrace::bindPrimitiveSP(const string& sym, boost::python::object sp)
{
  VentureValuePtr spRecord(new VentureSPRecord(new ForeignLiteSP(sp), new ForeignLiteSPAux(sp)));
  ConstantNode * node = trace->createConstantNode(spRecord);
  processMadeSP(trace.get(), node, false, false, shared_ptr<DB>(new DB()));
  assert(dynamic_pointer_cast<VentureSPRef>(trace->getValue(node)));
  trace->globalEnvironment->addBinding(sym, node);
}
