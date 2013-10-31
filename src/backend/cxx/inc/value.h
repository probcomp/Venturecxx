#ifndef VALUE_H
#define VALUE_H

#include <string>
#include <valarray>

/* Should be abstract. */
struct VentureValue { virtual ~VentureValue() {}; };

/* For "undefined" nodes in the Torus. */
struct VentureNone : VentureValue {};

/* For CSRReference nodes. */
struct VentureCSRReference : VentureValue {};

struct VentureBool : VentureValue 
{ 
  VentureBool(bool pred): pred(pred) {}; 
  bool pred;
};

struct VentureCount : VentureValue 
{ 
  VentureCount(uint32_t count): count(count) {}
  uint32_t count;
};

struct VentureSymbol : VentureValue 
{ 
  VentureSymbol(std::string sym): sym(sym) {}
  std::string sym;
};

struct VentureDouble : VentureValue 
{ 
  VentureDouble(double x): x(x) {}
  double x;
};

struct VentureAtom : VentureValue { unsigned int value; };
struct VentureSimplexPoint : VentureValue { std::valarray<double> ps; };

#endif


