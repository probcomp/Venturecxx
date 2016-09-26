// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"
#include "pyutils.h"
#include "serialize.h"

#include <boost/python.hpp>
#include <boost/python/extract.hpp>
#include <boost/python/object.hpp>
#include <boost/python/str.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>
#include <boost/thread.hpp>

struct VentureValue;

struct PyTrace
{
  PyTrace();
  ~PyTrace();

  void evalExpression(DirectiveID did, const boost::python::object & object);
  void unevalDirectiveID(DirectiveID did);

  void observe(DirectiveID did, const boost::python::object & valueExp);
  double unobserve(DirectiveID did);

  void bindInGlobalEnv(const string& sym, DirectiveID did);
  void unbindInGlobalEnv(const string& sym);
  bool boundInGlobalEnv(const string& sym);

  boost::python::object extractPythonValue(DirectiveID did);

  void bindPythonSP(const string& sym, const boost::python::object & sp);
  void bindPumaSP(const string& sym, SP* sp);

  void setSeed(size_t seed);
  size_t getSeed();

  uint32_t numUnconstrainedChoices();

  double makeConsistent();
  void registerConstraints();

  double logLikelihoodAt(
      const boost::python::object & pyscope,
      const boost::python::object & pyblock);
  double logJointAt(
      const boost::python::object & pyscope,
      const boost::python::object & pyblock);
  double likelihoodWeight();

  boost::python::list dotTrace(bool colorIgnored);

  // for testing
  int numNodesInBlock(
      const boost::python::object & scope,
      const boost::python::object & block);
  int numBlocksInScope(const boost::python::object & scope);
  boost::python::list numFamilies();

  double primitive_infer(const boost::python::dict & params);

  void freeze(DirectiveID did);

  PyTrace* stop_and_copy() const;

  shared_ptr<OrderedDB> makeEmptySerializationDB();
  shared_ptr<OrderedDB> makeSerializationDB(
      const boost::python::list & stackDicts,
      bool skipStackDictConversion);
  boost::python::list dumpSerializationDB(
      const shared_ptr<OrderedDB> & db,
      bool skipStackDictConversion);
  void unevalAndExtract(DirectiveID did, const shared_ptr<OrderedDB> & db);
  void restoreDirectiveID(DirectiveID did, const shared_ptr<OrderedDB> & db);
  void evalAndRestore(
      DirectiveID did,
      const boost::python::object & object,
      const shared_ptr<OrderedDB> & db);

  boost::python::list scope_keys();

private:
  shared_ptr<ConcreteTrace> trace;
};

#endif
