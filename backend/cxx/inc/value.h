#ifndef VALUE_H
#define VALUE_H

#include "debug.h"
#include "srs.h"
#include "all.h"

#include <string>
#include <valarray>
#include <iostream>
#include <unordered_map>
#include <vector>

#include <boost/python/object.hpp>
#include <boost/functional/hash.hpp>

struct SP;
struct Node;
struct SPAux;

/* Should be abstract. */
struct VentureValue { 
  virtual boost::python::object toPython() const { return boost::python::object("toPython() not implemented."); }

  virtual size_t toHash() const { assert(false); return 0; }
  virtual VentureValue * clone() const { assert(false); return nullptr; }

  virtual ~VentureValue() {}; 

  /* TODO this needs to be implemented for other types besides symbols. */
  virtual bool equals(const VentureValue * & other) const
    { assert(false); return false; } 
};

namespace std {
  template<>
  struct hash<VentureValue*> 
  {
    size_t operator()(const VentureValue * v) const
      { return v->toHash(); }
  };
  template<>
  struct equal_to<VentureValue*> 
  {
    bool operator()(const VentureValue* v1,const VentureValue* v2) const
      { return v1->equals(v2); }
  };
}

struct VentureSymbol : VentureValue
{
  VentureSymbol(const string & sym): sym(sym) {}
  string sym;
  size_t toHash() const override;
  VentureValue * clone() const override { return new VentureSymbol(sym); }
  bool equals(const VentureValue * & other) const override;
};

struct VentureList : VentureValue { };

struct VentureNil : VentureList { };

struct VenturePair : VentureList
{
  VenturePair(VentureValue * first, VentureList * rest): 
    first(first), rest(rest) {}
  VentureValue * first;
  VentureList * rest;
};

struct VentureMap : VentureValue
{ 
  unordered_map<VentureValue*,VentureValue*> map;
};

struct VentureBool : VentureValue 
{ 
  VentureBool(bool pred): pred(pred) {}; 
  boost::python::object toPython() const override { return boost::python::object(pred); }
  VentureValue * clone() const override { return new VentureBool(pred); }
  size_t toHash() const override { return hash<bool>()(pred); }
  bool pred;
};

struct VentureDouble : VentureValue 
{ 
  VentureDouble(double x): x(x) {}
  boost::python::object toPython() const override { return boost::python::object(x); }
  size_t toHash() const override { return hash<double>()(x); }
  VentureValue * clone() const override { return new VentureDouble(x); }
  double x;
};

struct VentureCount : VentureValue
{
  VentureCount(uint32_t n): n(n) {}
  boost::python::object toPython() const override { return boost::python::object(n); }
  size_t toHash() const override { return n; }
  VentureValue * clone() const override { return new VentureCount(n); }
  uint32_t n;
};

struct VentureVector : VentureValue
{
  VentureVector(const vector<VentureValue *> xs): xs(xs) {}
  boost::python::object toPython() const override { return boost::python::object("<vector>"); }
  vector<VentureValue *> xs;
};

/* RequestPSPs must return VentureRequests. */
struct VentureRequest : VentureValue
{
  VentureRequest() {}
  VentureRequest(vector<ESR> esrs): esrs(esrs) {}
  VentureRequest(vector<HSR *> hsrs): hsrs(hsrs) {}
  
  boost::python::object toPython() const override { return boost::python::object("<requests>"); }
  vector<ESR> esrs;
  vector<HSR *> hsrs;

  ~VentureRequest() { for (HSR * hsr : hsrs) { delete hsr; }  }
};

struct VentureSP : VentureValue
{
  VentureSP(SP * sp): sp(sp) {}
  SP * sp;
  Node * makerNode; // set in processMadeSP()

  ~VentureSP();

};



#endif


