#ifndef BUILT_IN_H
#define BUILT_IN_H

#include "value.h"

#include <map>
#include <vector>

map<string,VentureValue *> initBuiltInValues();
map<string,SP *> initBuiltInSPs();

#endif
