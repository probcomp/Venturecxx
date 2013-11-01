#ifndef VALUE_H
#define VALUE_H

#include "debug.h"
#include "srs.h"
#include "env.h"

#include <string>
#include <valarray>
#include <iostream>

using namespace std;

#include <boost/python/object.hpp>
#include <boost/functional/hash.hpp>

struct SP;
struct SPAux;

/* Should be abstract. */
struct VentureValue { 
  virtual boost::python::object toPython() { return boost::python::object("toPython() not implemented."); }
  virtual size_t toHash() { assert(false); return 0; }
  virtual ~VentureValue() {}; 
};

struct VentureBool : VentureValue 
{ 
  VentureBool(bool pred): pred(pred) {}; 
  boost::python::object toPython() override { return boost::python::object(pred); }
  size_t toHash() { return hash<bool>()(pred); }
  bool pred;
};

struct VentureDouble : VentureValue 
{ 
  VentureDouble(double x): x(x) {}
  boost::python::object toPython() override { return boost::python::object(x); }
  size_t toHash() { return hash<double>()(x); }
  double x;
};

struct VentureCount : VentureValue
{
  VentureCount(uint32_t n): n(n) {}
  boost::python::object toPython() override { return boost::python::object(n); }
  size_t toHash() { return n; }
  uint32_t n;
};

struct VentureVector : VentureValue
{
  VentureVector(const vector<VentureValue *> xs): xs(xs) {}
  boost::python::object toPython() override { return boost::python::object("<vector>"); }
  vector<VentureValue *> xs;
};

/* RequestPSPs must return VentureRequests. */
struct VentureRequest : VentureValue
{
  VentureRequest() {}
  VentureRequest(vector<ESR> esrs): esrs(esrs) {}
  VentureRequest(vector<HSR *> hsrs): hsrs(hsrs) {}
  
  boost::python::object toPython() override { return boost::python::object("<requests>"); }
  vector<ESR> esrs;
  vector<HSR *> hsrs;

  ~VentureRequest() { for (HSR * hsr : hsrs) { delete hsr; }  }
};

struct VentureEnvironment : VentureValue 
{ 
  VentureEnvironment(Environment env): env(env) {}
  Environment env;
};

struct VentureSP : VentureValue
{
  VentureSP(Node * makerNode, SP * sp): makerNode(makerNode), sp(sp) {}
  Node * makerNode;
  SP * sp;

  ~VentureSP();

};


#endif


