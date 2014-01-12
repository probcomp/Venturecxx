/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "pytrace.h"
#include <iostream>
#include <list>

PyTrace::PyTrace()
{
  jl_init(NULL);
  jl_function_t *f_ctrace = jl_get_function(jl_base_module, "CTrace"); // TODO FIX ME
  jl_trace = jl_call0(f_ctrace);

  JL_GC_PUSH1(&jl_trace);
}

PyTrace::~PyTrace()
{

}

jl_value_t * PyTrace::parseValue(boost::python::dict d)
{
  if (d["type"] == "boolean") { return jl_box_bool(boost::python::extract<bool>(d["value"])); }
  else if (d["type"] == "number") { return jl_box_float64(boost::python::extract<double>(d["value"])); }
  else if (d["type"] == "symbol") {
    // The cast at the return here appears to be fine, per
    // http://stackoverflow.com/questions/3766229/casting-one-struct-pointer-to-other-c
    return (jl_value_t*)jl_symbol(boost::python::extract<string>(d["value"])().c_str());
  }
  else if (d["type"] == "atom") { return jl_box_int32(boost::python::extract<uint32_t>(d["value"])); }
  else { assert(false); }
}

// TODO create a Julia array
jl_value_t * PyTrace::parseExpression(boost::python::object o)
{
  boost::python::extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return parseValue(getDict()); }
  
  boost::python::extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
 
  boost::python::ssize_t L = boost::python::len(l);
  jl_value_t* array_type = jl_apply_array_type(jl_any_type, 1);
  jl_array_t* exp = jl_alloc_array_1d(array_type, L);
  
  for(boost::python::ssize_t i=L;i > 0;i--) 
  {
    jl_arrayset(exp,parseExpression(l[i-1]),i-1);
  }
  return (jl_value_t*)exp;
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  jl_value_t * exp = parseExpression(o);

  jl_function_t *f_eval = jl_get_function(jl_base_module, "evalExpression"); // TODO FIX ME
  jl_value_t * id = jl_box_int64(directiveID);
  jl_call3(f_eval,jl_trace,id,exp);
}

void PyTrace::unevalDirectiveID(size_t directiveID)
{
  jl_function_t *f_uneval = jl_get_function(jl_base_module, "unevalExpression"); // TODO FIX ME
  jl_value_t * id = jl_box_int64(directiveID);
  jl_call2(f_uneval,jl_trace,id);
}

// TODO
boost::python::object PyTrace::extractPythonValue(size_t directiveID)
{
  assert(false);
}

void PyTrace::bindInGlobalEnv(string sym, size_t directiveID)
{
  jl_function_t *f_bind = jl_get_function(jl_base_module, "bindInGlobalEnv"); // TODO FIX ME
  jl_value_t * jsym = (jl_value_t*)jl_symbol(sym.c_str());
  jl_value_t * id = jl_box_int64(directiveID);
  jl_call3(f_bind,jl_trace,jsym,id);
}

void PyTrace::observe(size_t directiveID,boost::python::object valueExp)
{
  jl_function_t *f_observe = jl_get_function(jl_base_module, "observe"); // TODO FIX ME
  jl_value_t * id = jl_box_int64(directiveID);
  jl_value_t * val = parseExpression(valueExp);
  jl_call3(f_observe,jl_trace,id,val);
}

double PyTrace::getGlobalLogScore()
{
  assert(false);
  return 0;
}

uint32_t PyTrace::numRandomChoices()
{
  assert(false);
  return 0;
}

void PyTrace::unobserve(size_t directiveID)
{
  jl_function_t *f_unobserve = jl_get_function(jl_base_module, "unobserve"); // TODO FIX ME
  jl_value_t * id = jl_box_int64(directiveID);
  jl_call2(f_unobserve,jl_trace,id);
}

void PyTrace::set_seed(size_t n) {
  assert(false);
}

size_t PyTrace::get_seed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


void PyTrace::infer(boost::python::dict params) 
{ 
  jl_function_t *f_infer = jl_get_function(jl_base_module, "infer"); // TODO FIX ME
  jl_call2(f_infer,jl_trace,id); // TODO translate the params, make it so I can pass N
}


BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("uneval", &PyTrace::unevalDirectiveID)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("numRandomChoices", &PyTrace::numRandomChoices)
    .def("getGlobalLogScore", &PyTrace::getGlobalLogScore)
    .def("observe", &PyTrace::observe)
    .def("unobserve", &PyTrace::unobserve)
    .def("infer", &PyTrace::infer)
    .def("set_seed", &PyTrace::set_seed)
    .def("get_seed", &PyTrace::get_seed)
    ;
};

