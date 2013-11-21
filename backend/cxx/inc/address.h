#ifndef ADDRESS_H
#define ADDRESS_H

#include <iostream>
#include <cstdint>
#include "all.h"

struct SP;

// NOTE this is only for debugging
// To be correct, it would need to be indexed by the AUX, not the SP itself.
// but sp->name is helpful for debugging.
struct Address
{
  Address(SP * sp, size_t id, const string & path):
    sp(sp), id(id), path(path) {}

  friend ostream &operator<<(ostream & os, const Address & addr);

  Address add(string suffix);

  SP * sp;
  size_t id;
  string path;
};


#endif
