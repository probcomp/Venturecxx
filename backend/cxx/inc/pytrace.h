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
  
  void evalExpression(size_t did, boost::python::object object);
  void unevalDirectiveID(size_t directiveID);

  void observe(size_t did,boost::python::object valueExp);
  void unobserve(size_t directiveID);

  void bindInGlobalEnv(string sym, size_t did);

  boost::python::object extractPythonValue(size_t did);

  void setSeed(size_t seed);
  size_t getSeed();

  double getGlobalLogScore();
  uint32_t numRandomChoices();

  void infer(boost::python::dict params);

private:
  shared_ptr<Trace> trace;
  
};

#endif
