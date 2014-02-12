#include "expressions.h"
#include "values.h"

bool isVariable(VentureValuePtr exp) { return dynamic_pointer_cast<VentureSymbol>(exp); }
bool isSelfEvaluating(VentureValuePtr exp) { return !dynamic_pointer_cast<VentureArray>(exp); }
bool isQuotation(VentureValuePtr exp)
{ 
  shared_ptr<VentureArray> v_xs = dynamic_pointer_cast<VentureArray>(exp);
  assert(v_xs);
  shared_ptr<VentureSymbol> car = dynamic_pointer_cast<VentureSymbol>(v_xs->xs[0]);
  return car && car->s == "quote";
}

VentureValuePtr textOfQuotation(VentureValuePtr exp)
{ 
  shared_ptr<VentureArray> v_xs = dynamic_pointer_cast<VentureArray>(exp);
  assert(v_xs);
  return v_xs->xs[1];
}
