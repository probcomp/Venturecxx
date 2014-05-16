#ifndef TRACE_ADDRESS_H
#define TRACE_ADDRESS_H

#include "types.h"

struct Step { virtual ~Step(){} };
struct DefiniteFamilyStep : Step { DefiniteFamilyStep(DirectiveID index) : index(index){} DirectiveID index; };
struct OperatorStep : Step {};
struct OperandStep : Step { OperandStep(int index) : index(index){} int index; };
struct RequesterStep : Step {}; // From the output node to the request node
struct ESRStep : Step { ESRStep(FamilyID index) : index(index){} FamilyID index; };

struct TraceAddress
{
  TraceAddress(Step last);
  TraceAddress(AddrPtr previous, Step last);
  AddrPtr previous;
  Step last;
  size_t hash() const;
};

AddrPtr makeDefiniteFamilyAddress(DirectiveID index);
AddrPtr makeOperatorAddress(AddrPtr self);
AddrPtr makeOperandAddress(AddrPtr self, int index);
AddrPtr makeRequesterAddress(AddrPtr self);
AddrPtr makeESRAddress(AddrPtr self, FamilyID index);

/* for unordered map */
struct AddrPtrsEqual
{
  bool operator() (const AddrPtr& a, const AddrPtr& b) const
  {
    return a == b;
  }
};

struct HashAddrPtr
{
  size_t operator() (const AddrPtr& a) const
  {
    return a->hash();
  }
};

struct AddrPtrsLess
{
  bool operator() (const AddrPtr& a, const AddrPtr& b) const
  {
    return a < b;
  }
};

template <typename T>
class AddrPtrMap : public boost::unordered_map<AddrPtr, T, HashAddrPtr, AddrPtrsEqual> {};

#endif
