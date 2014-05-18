#include "indexer.h"
#include "value.h"
#include "values.h"
#include "scaffold.h"
#include "concrete_trace.h"

// TODO add assert from lite
ScaffoldIndexer::ScaffoldIndexer(ScopeID scope,BlockID block): scope(scope),block(block) {}
ScaffoldIndexer::ScaffoldIndexer(ScopeID scope,BlockID block,BlockID minBlock,BlockID maxBlock): scope(scope),block(block),minBlock(minBlock),maxBlock(maxBlock) {}

shared_ptr<Scaffold> ScaffoldIndexer::sampleIndex(ConcreteTrace * trace) const
{
  if (block->hasSymbol() && block->getSymbol() == "one")
    {
      BlockID actualBlock = trace->sampleBlock(scope);
      vector<set<Node*> > setsOfPNodes;
      setsOfPNodes.push_back(trace->getNodesInBlock(scope,actualBlock));
      shared_ptr<Scaffold> scaffold = constructScaffold(trace,setsOfPNodes,false);
      //cout << scaffold->showSizes() << endl;
      return scaffold;
    }
  else if (block->hasSymbol() && block->getSymbol() == "all")
    {
      vector<set<Node*> > setsOfPNodes;
      setsOfPNodes.push_back(trace->getAllNodesInScope(scope));
      return constructScaffold(trace,setsOfPNodes,false);
    }
  else if (block->hasSymbol() && block->getSymbol() == "ordered")
    {
      return constructScaffold(trace,trace->getOrderedSetsInScope(scope),false);
    }
  else if (block->hasSymbol() && block->getSymbol() == "ordered_range")
    {
      return constructScaffold(trace,trace->getOrderedSetsInScopeAndRange(scope,minBlock,maxBlock),false);
    }
  else
    {
      vector<set<Node*> > setsOfPNodes(1,trace->getNodesInBlock(scope,block));
      return constructScaffold(trace,setsOfPNodes,false);
    }
}


double ScaffoldIndexer::logDensityOfIndex(Trace * trace, shared_ptr<Scaffold> scaffold) const
{
  if (dynamic_pointer_cast<VentureSymbol>(block) && block->getSymbol() == "one")
  {
    return trace->logDensityOfBlock(scope);
  }
  else if (dynamic_pointer_cast<VentureSymbol>(block) && block->getSymbol() == "all") { return 0; }
  else if (dynamic_pointer_cast<VentureSymbol>(block) && block->getSymbol() == "ordered") { return 0; }
  else { return 0; }
}
