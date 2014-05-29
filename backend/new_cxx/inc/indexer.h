#ifndef INDEXER_H
#define INDEXER_H

#include "types.h"

struct Scaffold;
struct ConcreteTrace;
struct Trace;

struct ScaffoldIndexer
{
  ScaffoldIndexer(ScopeID scope,BlockID block);
  ScaffoldIndexer(ScopeID scope,BlockID block,BlockID minBlock,BlockID maxBlock);
  shared_ptr<Scaffold> sampleIndex(ConcreteTrace * trace) const;
  double logDensityOfIndex(Trace * trace, shared_ptr<Scaffold> scaffold) const;

  ScopeID scope;
  BlockID block;

  BlockID minBlock;
  BlockID maxBlock;
};


#endif
