#ifndef BUILTIN_H
#define BUILTIN_H

#include "types.h"
struct VentureSP;

map<string,VentureValuePtr> initBuiltInValues();
map<string,shared_ptr<VentureSP> > initBuiltInSPs();

#endif
