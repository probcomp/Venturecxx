#ifndef INDEXER_H
#define INDEXER_H

#include "types.h"

struct Scaffold;
struct ConcreteTrace;

struct ScaffoldIndexer
{
  ScaffoldIndexer(ScopeID scope,BlockID block);
  shared_ptr<Scaffold> sampleIndex(ConcreteTrace * trace) const;
  double logDensityOfIndex(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold) const;
};


#endif
