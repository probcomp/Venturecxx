#include "gkernels/func_mh.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "particle.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"

pair<Trace*,double> FuncMHGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;

  pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = p.first;
  rhoDB = p.second;

  assertTorus(scaffold);
  particle = shared_ptr<Particle>(new Particle(trace));

  double xiWeight = regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,rhoDB,shared_ptr<map<Node*,Gradient> >());

  return make_pair(particle.get(),xiWeight - rhoWeight);
}

void FuncMHGKernel::accept() { particle->commit(); }


void FuncMHGKernel::reject() { }
