#include "sps/lite.h"
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
    foreignOperandValues.append(args->operandValues[i]->toPython(args->trace));
  }
  boost::python::object foreignResult = psp.attr("simulate")(foreignOperandValues);
  return parseValue(boost::python::extract<boost::python::dict>(foreignResult));
}

double ForeignLitePSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->trace);
  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->trace));
  }
  boost::python::object foreignLogDensity = psp.attr("logDensity")(foreignValue, foreignOperandValues);
  return boost::python::extract<double>(foreignLogDensity);
}

void PyTrace::bindPrimitiveSP(const string& sym, boost::python::object sp)
{
  ConstantNode * node = trace->createConstantNode(VentureValuePtr(new VentureSPRecord(new ForeignLiteSP(sp))));
  processMadeSP(trace.get(), node, false, false, shared_ptr<DB>(new DB()));
  assert(dynamic_pointer_cast<VentureSPRef>(trace->getValue(node)));
  trace->globalEnvironment->addBinding(sym, node);
}
