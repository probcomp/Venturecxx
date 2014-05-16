#include "trace_address.h"

TraceAddress::TraceAddress(Step last) : last(last) {}
TraceAddress::TraceAddress(AddrPtr previous, Step last) : previous(previous), last(last) {}

AddrPtr extendAddress(AddrPtr self, Step last)
{
  return AddrPtr(new TraceAddress(self, last));
}

AddrPtr makeDefiniteFamilyAddress(DirectiveID index)
{
  return AddrPtr(new TraceAddress(DefiniteFamilyStep(index)));
}

AddrPtr makeOperatorAddress(AddrPtr self)
{
  return extendAddress(self, OperatorStep());
}
  
AddrPtr makeOperandAddress(AddrPtr self, int index)
{
  return extendAddress(self, OperandStep(index));
}

AddrPtr makeRequesterAddress(AddrPtr self)
{
  return extendAddress(self, RequesterStep());
}

AddrPtr makeESRAddress(AddrPtr self, FamilyID index)
{
  return extendAddress(self, ESRStep(index));
}

