#include "serialize.h"
#include "node.h"
#include "psp.h"
#include "trace.h"

OrderedDB::OrderedDB(Trace * trace, vector<VentureValuePtr> values) :
  trace(trace),
  stack(values) {}

OrderedDB::OrderedDB(Trace * trace) :
  trace(trace) {}

bool OrderedDB::hasValue(Node * node) { return true; }

VentureValuePtr OrderedDB::getValue(Node * node)
{
  if (DB::hasValue(node)) {
    return DB::getValue(node);
  }

  ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
  shared_ptr<PSP> psp = trace->getPSP(appNode);
  if (psp->isRandom()) {
    VentureValuePtr value = stack.back();
    stack.pop_back();
    // TODO: check if it's a Request, SPRef, or VentureEnvironment and raise an exception
    return value;
  }
  else {
    // resimulate deterministic PSPs
    shared_ptr<Args> args = trace->getArgs(appNode);
    return psp->simulate(args, 0);
  }
}

void OrderedDB::registerValue(Node * node, VentureValuePtr value)
{
  DB::registerValue(node, value);

  ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
  shared_ptr<PSP> psp = trace->getPSP(appNode);
  if (psp->isRandom()) {
    // TODO: check if it's a Request, SPRef, or VentureEnvironment and raise an exception
    stack.push_back(value);
  }
}
