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
    return VentureValuePtr(new VentureSPRecord(new ForeignLiteSP(thing["sp"]),
                                               new ForeignLiteSPAux(thing["aux"])));
  }
  else if (thing["type"] == "request")
  {
    boost::python::list foreignESRs = boost::python::extract<boost::python::list>(thing["value"]["esrs"]);
    boost::python::list foreignLSRs = boost::python::extract<boost::python::list>(thing["value"]["lsrs"]);
    vector<ESR> esrs;
    vector<shared_ptr<LSR> > lsrs;
    // TODO: ESRs
    for (boost::python::ssize_t i = 0; i < boost::python::len(foreignLSRs); ++i)
    {
      lsrs.push_back(shared_ptr<LSR>(new ForeignLiteLSR(foreignLSRs[i])));
    }
    return VentureValuePtr(new ForeignLiteRequest(esrs, lsrs));
  }
  else
  {
    return parseValue(boost::python::extract<boost::python::dict>(thing));
  }
}

boost::python::dict foreignArgsToPython(shared_ptr<Args> args)
{
  boost::python::dict foreignArgs;

  boost::python::list foreignOperandValues;
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    foreignOperandValues.append(args->operandValues[i]->toPython(args->_trace));
  }
  foreignArgs["operandValues"] = foreignOperandValues;

  boost::python::object foreignAux;
  if (shared_ptr<ForeignLiteSPAux> aux = dynamic_pointer_cast<ForeignLiteSPAux>(args->spAux))
  {
    foreignAux = aux->aux;
  }
  foreignArgs["spaux"] = foreignAux;

  OutputNode * outputNode = dynamic_cast<OutputNode*>(args->node);
  if (outputNode && args->_trace->hasAAAMadeSPAux(outputNode))
  {
    shared_ptr<SPAux> madeSPAux = args->_trace->getAAAMadeSPAux(outputNode);
    boost::python::object foreignMadeSPAux = dynamic_pointer_cast<ForeignLiteSPAux>(madeSPAux)->aux;
    foreignArgs["madeSPAux"] = foreignMadeSPAux;
  }

  // TODO: nodes, env, requests

  return foreignArgs;
}

VentureValuePtr ForeignLitePSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignResult = psp.attr("simulate")(foreignArgs);
  return foreignFromPython(foreignResult);
}

double ForeignLitePSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignLogDensity = psp.attr("logDensity")(foreignValue, foreignArgs);
  return boost::python::extract<double>(foreignLogDensity);
}

void ForeignLitePSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  psp.attr("incorporate")(foreignValue, foreignArgs);
}

void ForeignLitePSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  boost::python::dict foreignValue = value->toPython(args->_trace);
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  psp.attr("unincorporate")(foreignValue, foreignArgs);
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

shared_ptr<LKernel> const ForeignLitePSP::getAAALKernel()
{
  return shared_ptr<LKernel>(new ForeignLiteLKernel(psp.attr("getAAALKernel")()));
}

bool ForeignLitePSP::canEnumerateValues(shared_ptr<Args> args) const
{
  // TODO: Lite SPs do not seem to implement this usefully.
  return true;
}

vector<VentureValuePtr> ForeignLitePSP::enumerateValues(shared_ptr<Args> args) const
{
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignResult = psp.attr("enumerateValues")(foreignArgs);
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

VentureValuePtr ForeignLiteLKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng)
{
  boost::python::object foreignOldValue;
  if (oldValue)
  {
    foreignOldValue = oldValue->toPython(args->_trace);
  }
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignResult = lkernel.attr("simulate")(foreignOldValue, foreignArgs);
  return foreignFromPython(foreignResult);
}

double ForeignLiteLKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args)
{
  boost::python::dict foreignNewValue = newValue->toPython(args->_trace);
  boost::python::object foreignOldValue;
  if (oldValue)
  {
    foreignOldValue = oldValue->toPython(args->_trace);
  }
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignWeight = lkernel.attr("weight")(foreignNewValue, foreignOldValue, foreignArgs);
  return boost::python::extract<double>(foreignWeight);
}

double ForeignLiteLKernel::reverseWeight(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args)
{
  boost::python::dict foreignOldValue = oldValue->toPython(args->_trace);
  boost::python::dict foreignArgs = foreignArgsToPython(args);
  boost::python::object foreignWeight = lkernel.attr("reverseWeight")(foreignOldValue, foreignArgs);
  return boost::python::extract<double>(foreignWeight);
}

boost::python::dict ForeignLiteRequest::toPython(Trace * trace) const
{
  boost::python::list foreignESRs;
  boost::python::list foreignLSRs;
  // TODO: ESRs
  for (size_t i = 0; i < lsrs.size(); ++i)
  {
    foreignLSRs.append(dynamic_pointer_cast<ForeignLiteLSR>(lsrs[i])->lsr);
  }
  boost::python::dict value;
  value["esrs"] = foreignESRs;
  value["lsrs"] = foreignLSRs;
  boost::python::dict stackDict;
  stackDict["type"] = "request";
  stackDict["value"] = value;
  return stackDict;
}

shared_ptr<LatentDB> ForeignLiteSP::constructLatentDB() const
{
  return shared_ptr<LatentDB>(new ForeignLiteLatentDB(sp.attr("constructLatentDB")()));
}

double ForeignLiteSP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const
{
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(spaux)->aux;
  boost::python::object foreignLSR = dynamic_pointer_cast<ForeignLiteLSR>(lsr)->lsr;
  boost::python::object foreignLatentDB;
  if (latentDB)
  {
    foreignLatentDB = dynamic_pointer_cast<ForeignLiteLatentDB>(latentDB)->latentDB;
  }
  return boost::python::extract<double>(sp.attr("simulateLatents")(foreignAux, foreignLSR, shouldRestore, foreignLatentDB));
}

double ForeignLiteSP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const
{
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(spaux)->aux;
  boost::python::object foreignLSR = dynamic_pointer_cast<ForeignLiteLSR>(lsr)->lsr;
  boost::python::object foreignLatentDB = dynamic_pointer_cast<ForeignLiteLatentDB>(latentDB)->latentDB;
  return boost::python::extract<double>(sp.attr("detachLatents")(foreignAux, foreignLSR, foreignLatentDB));
}

boost::python::dict ForeignLiteSP::toPython(Trace * trace, shared_ptr<SPAux> aux) const
{
  boost::python::object foreignAux = dynamic_pointer_cast<ForeignLiteSPAux>(aux)->aux;
  // TODO: make this transparent if possible
  boost::python::dict stackDict;
  stackDict["type"] = "foreign_sp";
  stackDict["sp"] = sp;
  stackDict["aux"] = foreignAux;
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
