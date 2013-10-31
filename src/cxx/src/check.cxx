#include "check.h"

void assertTorus(Trace * trace, Scaffold * scaffold)
{
  for (std::pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    assert(!p.first->isActive);
    assert(p.second.regenCount == 0);
  }
}

void assertWhole(Trace * trace, Scaffold * scaffold)
{
  //assert(false);
}
