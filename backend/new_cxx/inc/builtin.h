#ifndef BUILTIN_H
#define BUILTIN_H

#include "types.h"
struct SP;

map<string,VentureValuePtr> initBuiltInValues();
map<string,SP *> initBuiltInSPs();

#endif
