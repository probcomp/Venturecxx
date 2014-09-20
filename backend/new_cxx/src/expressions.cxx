#include "expressions.h"
#include "values.h"

bool isVariable(VentureValuePtr exp) { return dynamic_pointer_cast<VentureSymbol>(exp) != NULL; }
bool isSelfEvaluating(VentureValuePtr exp) { return !exp->hasArray() || dynamic_pointer_cast<VentureVector>(exp); }
bool isQuotation(VentureValuePtr exp)
{ 
  assert(exp->hasArray());
  vector<VentureValuePtr> xs = exp->getArray();
  assert(!xs.empty());
  return xs[0]->hasSymbol() && xs[0]->getSymbol() == "quote";
}

VentureValuePtr textOfQuotation(VentureValuePtr exp)
{ 
  assert(exp->hasArray());
  vector<VentureValuePtr> xs = exp->getArray();
  assert(!xs.empty());
  return xs[1];
}
