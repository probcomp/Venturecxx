#include "sps/lite.h"
#include "sprecord.h"
#include "pyutils.h"
#include "pytrace.h"
#include "concrete_trace.h"
#include "regen.h"
#include "env.h"

VentureValuePtr ForeignLitePSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignResult = psp.attr("simulate")(foreignOperandValues);
  if (foreignResult.attr("__class__").attr("__name__") == "ForeignLiteSP")
  {
    return VentureValuePtr(new VentureSPRecord(new ForeignLiteSP(foreignResult)));
  }
  else
  {
    return parseValue(boost::python::extract<boost::python::dict>(foreignResult));
  }
}

double ForeignLitePSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  boost::python::object foreignLogDensity = psp.attr("logDensity")(foreignValue, foreignOperandValues);
  return boost::python::extract<double>(foreignLogDensity);
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
  boost::python::object foreignResult = psp.attr("enumerateValues")(foreignOperandValues);
  boost::python::list foreignValues = boost::python::extract<boost::python::list>(foreignResult);
  vector<VentureValuePtr> values;
  for (boost::python::ssize_t i = 0; i < boost::python::len(foreignValues); ++i)
  {
    values.push_back(parseValue(boost::python::extract<boost::python::dict>(foreignValues[i])));
  }
  return values;
}

void PyTrace::bindPrimitiveSP(const string& sym, boost::python::object sp)
{
  ConstantNode * node = trace->createConstantNode(VentureValuePtr(new VentureSPRecord(new ForeignLiteSP(sp))));
  processMadeSP(trace.get(), node, false, false, shared_ptr<DB>(new DB()));
  assert(dynamic_pointer_cast<VentureSPRef>(trace->getValue(node)));
  trace->globalEnvironment->addBinding(sym, node);
}
