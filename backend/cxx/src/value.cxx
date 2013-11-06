#include "value.h"
#include "sp.h"
#include <typeinfo>


std::string ignore_typeid_name = "2SP";


VentureSP::~VentureSP() 
{ 
  std::string this_typeid_name = (std::string) typeid(*sp).name();
  if(this_typeid_name == ignore_typeid_name) {
    // std::cout << "VentureSP::~VentureSP : NOT deleting sp named " << this_typeid_name << std::endl;
  } else {
    // std::cout << "VentureSP::~VentureSP : DELETING sp named " << this_typeid_name << std::endl;
    delete sp;
  }
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
