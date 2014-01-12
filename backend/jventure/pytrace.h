#ifndef PY_TRACE_H
#define PY_TRACE_H

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>
#include <julia.h>

using namespace std;

struct PyTrace
{
  PyTrace();
  ~PyTrace();
  
  jl_value_t * parseValue(boost::python::dict d);
  jl_value_t * parseExpression(boost::python::object o);

  void evalExpression(size_t did, boost::python::object object);
  void bindInGlobalEnv(string sym, size_t did);
  boost::python::object extractPythonValue(size_t did);
  void observe(size_t did,boost::python::object valueExp);

  void unevalDirectiveID(size_t directiveID);
  void unobserve(size_t directiveID);

  void set_seed(size_t seed);
  size_t get_seed();

  double getGlobalLogScore();
  uint32_t numRandomChoices();

  void infer(boost::python::dict params);
  
  jl_value_t * jl_trace;


};

#endif
