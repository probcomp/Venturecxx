#include "check.h"
#include "node.h"
#include "trace.h"
#include "scaffold.h"
#include "node.h"

void TraceConsistencyChecker::checkConsistency()
{
//  uint32_t numUCRCs = 0;  // unconstrained random choices
//  uint32_t numCRCs = 0;   // constrained random choices

//  map<pair<Node *,size_t>, Node *> spFamilies;
  
//  map<size_t,pair<Node*,VentureValue*> > ventureFamilies;

  // Iterate over each Venture family, 
//  for (pair<size_t,pair<Node*,VentureValue*> > pp : ventureFamilies)
//  {
//    Node * root = pp.second.first;
    
    



//  }

  assert(false);
}



void TraceConsistencyChecker::checkTorus(Scaffold * scaffold)
{
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    if (p.second.regenCount != 0) { scaffold->show(); assert(false); }
  }

}

void TraceConsistencyChecker::checkWhole(Scaffold * scaffold)
{
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    assert(p.second.regenCount > 0);
  }
}

