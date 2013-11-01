#include "value.h"
#include "sp.h"

#include <typeinfo>

VentureSP::~VentureSP() 
{ 
  delete sp; 
}
