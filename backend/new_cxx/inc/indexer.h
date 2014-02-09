#ifndef INDEXER_H
#define INDEXER_H

struct ScaffoldIndexer
{
  ScaffoldIndexer(ScopeID scope,BlockID block);
  shared_ptr<Scaffold> sampleIndex(ConcreteTrace * trace) const;
  double logDensityOfIndex(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold) const;
};


#endif
