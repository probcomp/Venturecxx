#ifndef TRACE_ADDRESS_H
#define TRACE_ADDRESS_H

#include "types.h"

class Step { virtual ~Step(); };
class OperatorStep : Step {};
class OperandStep : Step { int index; };
class RequesterStep : Step {}; // From the output node to the request node
class ESRStep : Step { FamilyID index; }

struct TraceAddress
{
  vector<Step> path;
};

#endif
