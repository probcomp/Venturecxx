#ifndef PYSP_H
#define PYSP_H

#include "sp.h"

#include <boost/python/wrapper.hpp>
#include <boost/python/list.hpp>

struct PySP: SP, boost::python::wrapper<SP>
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  boost::python::object simulateOutputPython(boost::python::list args) const;

};


#endif
