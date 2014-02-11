bool isVariable(VentureValuePtr exp) { return dynamic_pointer_cast<VentureSymbol>(exp); }
bool isSelfEvaluating(VentureValuePtr exp) { return !dynamic_pointer_cast<VentureArray>(exp); }
bool isQuotation(VentureValuePtr exp)
{ 
  v_xs = dynamic_pointer_cast<VentureArray>(exp);
  assert(v_xs);
  return v_xs->xs[0] == "quote";
}

VentureValuePtr textOfQuotation(VentureValuePtr exp)
{ 
  v_xs = dynamic_pointer_cast<VentureArray>(exp);
  assert(v_xs);
  return v_xs->xs[1];
}
