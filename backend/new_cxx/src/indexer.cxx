#include "indexer.h"
#include "value.h"
#include "values.h"
#include "scaffold.h"
#include "concrete_trace.h"

// TODO add assert from lite
ScaffoldIndexer::ScaffoldIndexer(ScopeID scope,BlockID block): scope(scope),block(block) {}

shared_ptr<Scaffold> ScaffoldIndexer::sampleIndex(ConcreteTrace * trace) const
{
  if (dynamic_pointer_cast<VentureSymbol>(block) && block->getSymbol() == "one")
  {
    BlockID actualBlock = trace->sampleBlock(scope);
    vector<set<Node*> > setsOfPNodes;
    setsOfPNodes.push_back(trace->getNodesInBlock(scope,actualBlock));
    return constructScaffold(trace,setsOfPNodes);
  }
  else { assert(false); }
}


double ScaffoldIndexer::logDensityOfIndex(Trace * trace, shared_ptr<Scaffold> scaffold) const
{
  if (dynamic_pointer_cast<VentureSymbol>(block) && block->getSymbol() == "one")
  {
    return trace->logDensityOfBlock(scope);
  }
  else { assert(false); }
}
