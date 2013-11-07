#include "value.h"
#include "sp.h"

#include <iostream>

VentureSP::~VentureSP() 
{ 
  cout << "Deleting SP(" << sp << ")" << endl;
  delete sp; 
}


size_t VentureSymbol::toHash() const 
{ 
  return hash<string>()(sym); 
}

bool VentureSymbol::equals(const VentureValue * & other) const 
{ 
  const VentureSymbol * vsym = dynamic_cast<const VentureSymbol*>(other);
  return vsym && vsym->sym == sym;
}

string VentureSP::toString() const
{
  return sp->name;
}
