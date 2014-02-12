#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"
#include "pyutils.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>
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

  void bindInGlobalEnv(string sym, size_t did);

  boost::python::object extractPythonValue(DirectiveID did);

  void setSeed(size_t seed);
  size_t getSeed();

  double getGlobalLogScore();
  uint32_t numRandomChoices();

  void infer(boost::python::dict params);

private:
  shared_ptr<ConcreteTrace> trace;
  
};

#endif
