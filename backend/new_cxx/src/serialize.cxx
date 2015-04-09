// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "serialize.h"
#include "node.h"
#include "psp.h"
#include "trace.h"
#include "pytrace.h"
#include "concrete_trace.h"
#include "detach.h"
#include "regen.h"

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

shared_ptr<OrderedDB> PyTrace::makeEmptySerializationDB()
{
  return shared_ptr<OrderedDB>(new OrderedDB(trace.get()));
}

shared_ptr<OrderedDB> PyTrace::makeSerializationDB(boost::python::list stackDicts, bool skipStackDictConversion)
{
  assert(!skipStackDictConversion);

  vector<VentureValuePtr> values;
  for (boost::python::ssize_t i = 0; i < boost::python::len(stackDicts); ++i)
  {
    values.push_back(parseValue(boost::python::extract<boost::python::dict>(stackDicts[i])));
  }

  return shared_ptr<OrderedDB>(new OrderedDB(trace.get(), values));
}

boost::python::list PyTrace::dumpSerializationDB(shared_ptr<OrderedDB> db, bool skipStackDictConversion)
{
  assert(!skipStackDictConversion);

  vector<VentureValuePtr> values = db->listValues();
  boost::python::list stackDicts;
  for (size_t i = 0; i < values.size(); ++i)
  {
    stackDicts.append(values[i]->toPython(trace.get()));
  }

  return stackDicts;
}

void PyTrace::unevalAndExtract(DirectiveID did, shared_ptr<OrderedDB> db)
{
  // leaves trace in an inconsistent state. use restore afterward
  assert(trace->families.count(did));
  unevalFamily(trace.get(),
               trace->families[did].get(),
               shared_ptr<Scaffold>(new Scaffold()),
               db);
}

void PyTrace::restoreDirectiveID(DirectiveID did, shared_ptr<OrderedDB> db)
{
  assert(trace->families.count(did));
  restore(trace.get(),
          trace->families[did].get(),
          shared_ptr<Scaffold>(new Scaffold()),
          db,
          shared_ptr<map<Node*,Gradient> >());
}

void PyTrace::evalAndRestore(DirectiveID did, boost::python::object object, shared_ptr<OrderedDB> db)
{
  VentureValuePtr exp = parseExpression(object);
  pair<double,Node*> p = evalFamily(trace.get(),
                                    exp,
                                    trace->globalEnvironment,
                                    shared_ptr<Scaffold>(new Scaffold()),
                                    true,
                                    db,
                                    shared_ptr<map<Node*,Gradient> >());
  assert(p.first == 0);
  assert(!trace->families.count(did));
  trace->families[did] = shared_ptr<Node>(p.second);
}
