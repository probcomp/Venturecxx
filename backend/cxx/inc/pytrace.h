#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>

struct VentureValue;
struct GKernel;

/* Is a friend of Trace. Probably better to extend trace instead. */
struct PyTrace : Trace
{
  PyTrace();
  ~PyTrace();

  VentureValue * parseValue(boost::python::dict d);
  VentureValue * parseExpression(boost::python::object o);

  void evalExpression(size_t did, boost::python::object object);
  void bindInGlobalEnv(string sym, size_t did);
  boost::python::object extractPythonValue(size_t did);
  void observe(size_t did,boost::python::object valueExp);
//  void unobserve(size_t did);

  void set_seed(size_t seed);
  size_t get_seed();

  void unevalDirectiveID(size_t directiveID);
  void unobserve(size_t directiveID);

  double getGlobalLogScore();


  void infer(boost::python::dict options);

  map<string,GKernel *> gkernels;

  

};


#endif
