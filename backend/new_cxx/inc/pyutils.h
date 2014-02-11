#ifndef PYUTILS_H
#define PYUTILS_H

#include <boost/python.hpp>
#include <boost/python/object.hpp>
#include <boost/python/list.hpp>
#include <boost/python/dict.hpp>

struct VentureValue;

VentureValue * parseValue(boost::python::dict d);
VentureValue * parseExpression(boost::python::object o);


#endif
