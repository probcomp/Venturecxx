#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>


struct VentureValue;
struct GKernel;

struct PyTrace : Trace
{
  PyTrace();
  ~PyTrace();

  void evalExpression(size_t did, boost::python::object object);
  void bindInGlobalEnv(string sym, size_t did);
  boost::python::object extractPythonValue(size_t did);
  void observe(size_t did,boost::python::object valueExp);
//  void unobserve(size_t did);

  void set_seed(size_t seed);
  size_t get_seed();

  void infer(boost::python::dict options);

  map<string,GKernel *> gkernels;
};


#endif
