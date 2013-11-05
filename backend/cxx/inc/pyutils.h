#ifndef PYUTILS_H
#define PYUTILS_H

struct VentureValue;

#include <boost/python/object.hpp>
#include <boost/python/dict.hpp>

VentureValue * parseValue(boost::python::dict d);
VentureValue * parseExpression(boost::python::object o);


#endif
