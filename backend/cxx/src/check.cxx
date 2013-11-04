#include "check.h"
#include "node.h"
#include "trace.h"
#include "scaffold.h"
#include "node.h"

void assertTorus(Trace * trace, Scaffold * scaffold)
{
  bool fail = false;
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    if (p.first->isActive) { fail = true; }
    if (p.second.regenCount != 0) { fail = true; }
  }
  assert(!fail);
}

void assertWhole(Trace * trace, Scaffold * scaffold)
{
  for (pair<Node *,Scaffold::DRGNode> p : scaffold->drg)
  {
    assert(p.first->isActive);
    assert(p.second.regenCount > 0);
  }
}

