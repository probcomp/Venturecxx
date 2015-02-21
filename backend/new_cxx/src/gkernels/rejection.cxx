#include "gkernels/rejection.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"

pair<Trace*,double> BogoPossibilizeGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  
  assert(scaffold->border.size() == 1);
  while (true) {
    pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
    double rhoWeight = p.first;
    rhoDB = p.second;

    assertTorus(scaffold);

    double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,rhoDB,shared_ptr<map<Node*,Gradient> >());
    cout << rhoWeight << ", " << xiWeight << endl;
    if (rhoWeight > -INFINITY) {
      // The original state was possible; force rejecting the transition
      return make_pair(trace, -INFINITY);
    } else if (xiWeight > -INFINITY) {
      // Moving from impossible to possible state; force accepting the
      // transition
      return make_pair(trace, INFINITY);
    } else {
      this->reject(); // To restore everything to its proper state TODO use particles?
    }
  }
}

void BogoPossibilizeGKernel::accept() { }


void BogoPossibilizeGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
