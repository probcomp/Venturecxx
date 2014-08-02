#ifndef PYUTILS_H
#define PYUTILS_H

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>

#include "types.h"

VentureValuePtr fromPython(boost::python::object o);
VentureValuePtr parseValue(boost::python::dict d);
VentureValuePtr parseExpression(boost::python::object o);


#endif
