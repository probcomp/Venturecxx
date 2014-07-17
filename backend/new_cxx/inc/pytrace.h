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
  
  void evalExpression(DirectiveID did, boost::python::object object);
  void unevalDirectiveID(DirectiveID did);

  void observe(DirectiveID did,boost::python::object valueExp);
  void unobserve(DirectiveID did);

  void bindInGlobalEnv(const string& sym, DirectiveID did);
  void unbindInGlobalEnv(const string& sym);

  boost::python::object extractPythonValue(DirectiveID did);

  void bindPrimitiveSP(const string& sym, boost::python::object sp);

  void setSeed(size_t seed);
  size_t getSeed();

  double getDirectiveLogScore(DirectiveID did);
  double getGlobalLogScore();
  uint32_t numUnconstrainedChoices();

  double makeConsistent();

  boost::python::list dotTrace(bool colorIgnored);

  // for testing
  int numNodesInBlock(boost::python::object scope, boost::python::object block);
  boost::python::list numFamilies();

  void infer(boost::python::dict params);
  
  boost::python::dict continuous_inference_status();
  void start_continuous_inference(boost::python::dict params);
  void stop_continuous_inference();

  void freeze(DirectiveID did);

  PyTrace* stop_and_copy() const;

  shared_ptr<OrderedDB> makeEmptySerializationDB();
  shared_ptr<OrderedDB> makeSerializationDB(boost::python::list stackDicts, bool skipStackDictConversion);
  boost::python::list dumpSerializationDB(shared_ptr<OrderedDB> db, bool skipStackDictConversion);
  void unevalAndExtract(DirectiveID did, shared_ptr<OrderedDB> db);
  void restoreDirectiveID(DirectiveID did, shared_ptr<OrderedDB> db);
  void evalAndRestore(DirectiveID did, boost::python::object object, shared_ptr<OrderedDB> db);

  boost::python::list scope_keys();

private:
  shared_ptr<ConcreteTrace> trace;
  
  bool continuous_inference_running;
  boost::python::dict continuous_inference_params;
  boost::thread * continuous_inference_thread;

};

#endif
