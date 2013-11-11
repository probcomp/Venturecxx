#ifndef PY_TRACE_H
#define PY_TRACE_H

#include "trace.h"

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>
#include <thread>

struct VentureValue;
struct MixMHKernel;

struct PyTrace
{
  PyTrace();
  ~PyTrace();
  
  void evalExpression(size_t did, boost::python::object object);
  void bindInGlobalEnv(string sym, size_t did);
  boost::python::object extractPythonValue(size_t did);
  void observe(size_t did,boost::python::object valueExp);

  void unevalDirectiveID(size_t directiveID);
  void unobserve(size_t directiveID);

  void set_seed(size_t seed);
  size_t get_seed();

  void bindPySP(string module_str, string pysp_name);
  std::vector<boost::python::object> pysp_objects_vec;

  double getGlobalLogScore();
  uint32_t numRandomChoices();

  Trace * trace;
  map<pair<string,bool> ,MixMHKernel *> gkernels;

  void infer(boost::python::dict options);
  
  boost::python::dict continuous_inference_status();
  void start_continuous_inference(boost::python::dict params);
  void stop_continuous_inference();

  
  bool continuous_inference_running = false;
  boost::python::dict continuous_inference_params;
  std::thread * continuous_inference_thread;
};

void run_continuous_inference(MixMHKernel * gkernel, bool * flag);  

#endif
