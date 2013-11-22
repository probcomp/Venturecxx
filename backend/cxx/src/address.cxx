#include "address.h"
#include "sp.h"
#include <iostream>

ostream &operator<<(ostream & os, const Address & addr)
{ 
  if (addr.sp) {
    os << "<" << addr.sp->name 
       << ", " << addr.sp 
       << ", " << addr.id 
       << ", " << addr.path
       << ">";
  }
  else 
  {
    os << "<" << "venture"
       << ", " << addr.id 
       << ", " << addr.path
       << ">";
  }

  return os;            
}

Address Address::add(string suffix)
{
  return Address(sp,id,path + suffix);
}
