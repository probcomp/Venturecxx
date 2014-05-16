#ifndef TRACE_ADDRESS_H
#define TRACE_ADDRESS_H

#include "types.h"

struct Step { virtual ~Step(){} };
struct OperatorStep : Step {};
struct OperandStep : Step { OperandStep(int index) : index(index){} int index; };
struct RequesterStep : Step {}; // From the output node to the request node
struct ESRStep : Step { ESRStep(FamilyID index) : index(index){} FamilyID index; };

struct TraceAddress
{
  TraceAddress(shared_ptr<TraceAddress> previous, Step last);
  shared_ptr<TraceAddress> previous;
  Step last;
};

shared_ptr<TraceAddress> makeOperatorAddress(shared_ptr<TraceAddress> self);
shared_ptr<TraceAddress> makeOperandAddress(shared_ptr<TraceAddress> self, int index);
shared_ptr<TraceAddress> makeRequesterAddress(shared_ptr<TraceAddress> self);
shared_ptr<TraceAddress> makeESRAddress(shared_ptr<TraceAddress> self, FamilyID index);

#endif
