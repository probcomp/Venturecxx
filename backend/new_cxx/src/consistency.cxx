#include "consistency.h"
#include "scaffold.h"
#include "trace.h"

void assertTorus(shared_ptr<Scaffold> scaffold)
{
  for (map<Node*,int>::iterator iter = scaffold->regenCounts.begin();
       iter != scaffold->regenCounts.end();
       ++iter)
  {
    assert(iter->second == 0);
  }
}

void assertTrace(Trace * trace,shared_ptr<Scaffold> scaffold)
{
  for (map<Node*,int>::iterator iter = scaffold->regenCounts.begin();
       iter != scaffold->regenCounts.end();
       ++iter)
  {
    assert(iter->second > 0);
  }
}
