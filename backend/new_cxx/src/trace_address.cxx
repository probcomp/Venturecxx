#include "trace_address_h"

TraceAddress::TraceAddress(shared_ptr<TraceAddress> previous, Step last) : previous(previous), last(last) {}

shared_ptr<TraceAddress> extendAddress(shared_ptr<TraceAddress> self, Step last)
{
  return shared_ptr<TraceAddress>(new TraceAddress(self, last));
}

shared_ptr<TraceAddress> makeOperatorAddress(shared_ptr<TraceAddress> self)
{
  return extendAddress(self, OperatorStep());
}
  
shared_ptr<TraceAddress> makeOperandAddress(shared_ptr<TraceAddress> self, int index)
{
  return extendAddress(self, OperandStep(index));
}

shared_ptr<TraceAddress> makeRequesterAddress(shared_ptr<TraceAddress> self)
{
  return extendAddress(self, RequesterStep());
}

shared_ptr<TraceAddress> makeESRAddress(shared_ptr<TraceAddress> self, FamilyID index)
{
  return extendAddress(self, ESRStep(FamilyID));
}

