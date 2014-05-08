#include "gkernels/inplace.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"
#include <ctime>

using std::function;
using std::pair;

InPlaceGKernel::InPlaceGKernel() {
	
}

double InPlaceGKernel::prepare(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold, bool compute_gradient) {
  pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold, compute_gradient);
  double rhoWeight = p.first;
  rhoDB = p.second;
  assertTorus(scaffold);
  return rhoWeight;
}

void InPlaceGKernel::accept() { }


void InPlaceGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
