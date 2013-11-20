#include "spaux.h"
#include <iostream>
#include <cassert>

SPAux::SPAux()
{
}


SPAux::~SPAux() 
{ 
  assert(isValid()); 
  magic = 0;
}

SPAux * SPAux::clone() const
{
  assert(false);
  return nullptr;
}
