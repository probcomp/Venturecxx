#ifndef BUILTIN_H
#define BUILTIN_H

#include "types.h"
#include <map>
using std::map;

map<string,VentureValuePtr> initBuiltInValues();
map<string,shared_ptr<VentureSP> > initBuiltInSPs();

#endif
