#include "indexer.h"

ScaffoldIndexer::ScaffoldIndexer(ScopeID scope,BlockID block) { throw 500; }
shared_ptr<Scaffold> ScaffoldIndexer::sampleIndex(ConcreteTrace * trace) const { throw 500; }
double ScaffoldIndexer::logDensityOfIndex(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold) const { throw 500;}
