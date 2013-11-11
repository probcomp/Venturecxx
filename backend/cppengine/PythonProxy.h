
#ifndef VENTURE___PYTHON_PROXY_H
#define VENTURE___PYTHON_PROXY_H

#include "Header.h"

#include "VentureValues.h"
#include "VentureParser.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "XRPCore.h"
#include "MHProposal.h"
#include "RIPL.h"
#include "ERPs.h"
#include "Primitives.h"
#include "PythonProxy.h"

extern int VENTURE_GLOBAL__current_random_seed;

class handling_python_error : std::runtime_error {
public:
  handling_python_error();
};

string PythonObjectAsString(PyObject* python_object);

bool ConvertPythonObjectToVentureValue
  (PyObject* python_object,
   shared_ptr<VentureValue>* pointer_to_shared_pointer);

bool ConvertPythonObjectToVentureValue_internal
  (PyObject* python_object,
   shared_ptr<VentureValue>* pointer_to_shared_pointer);
   
PyObject*
ForPython__report_value(PyObject *self, PyObject *args);

PyObject*
ForPython__report_directives(PyObject *self, PyObject *args);

PyObject*
ForPython__clear(PyObject *self, PyObject *args);

PyObject*
ForPython__forget(PyObject *self, PyObject *args);

PyObject*
ForPython__infer(PyObject *self, PyObject *args);

PyObject*
ForPython__start_continuous_inference(PyObject *self, PyObject *args);

PyObject*
ForPython__continuous_inference_status(PyObject *self, PyObject *args);

PyObject*
ForPython__stop_continuous_inference(PyObject *self, PyObject *args);

PyObject*
ForPython__assume(PyObject *self, PyObject *args);

PyObject*
ForPython__predict(PyObject *self, PyObject *args);

PyObject*
ForPython__observe(PyObject *self, PyObject *args);

PyObject*
ForPython__draw_graph_to_file(PyObject *self, PyObject *args);

PyObject*
ForPython__logscore(PyObject *self, PyObject *args);

PyObject*
ForPython__get_seed(PyObject *self, PyObject *args);

PyObject*
ForPython__set_seed(PyObject *self, PyObject *args);

PyObject*
ForPython__get_entropy_info(PyObject *self, PyObject *args);

#ifdef _VENTURE_USE_GOOGLE_PROFILER
PyObject*
ForPython___start_profiler(PyObject *self, PyObject *args);
PyObject*
ForPython___stop_profiler(PyObject *self, PyObject *args);
#endif

PyObject*
ForPython___exit(PyObject *self, PyObject *args);

extern PyMethodDef MethodsForPythons[];

shared_ptr< VenturePythonObject > ExecutePythonFunction(
  string module_name_as_string,
  string function_name,
  vector< shared_ptr<VentureValue> > arguments);

#endif
