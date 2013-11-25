#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"
#include "render.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>
#include <thread>

struct VentureValue;
struct MixMHKernel;

void run_continuous_inference(MixMHKernel * gkernel, bool * flag);  

struct PyTrace
{
  PyTrace();
  ~PyTrace();
  
  VentureValue * parseValue(boost::python::dict d);
  VentureValue * parseExpression(boost::python::object o);

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
  
  boost::python::dict continuous_inference_status();
  void start_continuous_inference(boost::python::dict params);
  void stop_continuous_inference();

  Trace * trace;
  map<pair<string,bool> ,MixMHKernel *> gkernels;
  
  bool continuous_inference_running = false;
  boost::python::dict continuous_inference_params;
  std::thread * continuous_inference_thread;

  // TODO skipping scaffold for now
  string dotTrace();
};

#endif
