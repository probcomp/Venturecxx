#include "gkernels/slice.h"
#include <ctime>
#include "psp.h"
#include "scaffold.h"
#include "lkernel.h"
#include "particle.h"
#include "regen.h"
#include "detach.h"
#include "concrete_trace.h"
#include "db.h"
#include "consistency.h"
#include "rng.h"

double SliceGKernel::computeLogDensity(double x)
{
  Node * node = static_cast<Node*>(pnode);
  trace->registerLKernel(scaffold,node,shared_ptr<LKernel>(new DeterministicLKernel(VentureValuePtr(new VentureNumber(x)),psp)));

  /* The density is with respect to fixed entropy */
  shared_ptr<RNGbox> rng(new RNGbox(gsl_rng_mt19937));
  rng->set_seed(seed);

  shared_ptr<Particle> p = shared_ptr<Particle>(new Particle(trace,rng));

  return regenAndAttach(p.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),shared_ptr<map<Node*,Gradient> >());
}

double SliceGKernel::sliceSample(double x0, double w, int m, double lower, double upper)
{
  cout << "Slicing with x0 " << x0 << " w " << w << " m " << m << " lower " << lower << " upper " << upper << endl;
  double gx0 = computeLogDensity(x0);
  double logy = gx0 + log(gsl_ran_flat(trace->getRNG(),0.0,1.0));

  double u = gsl_ran_flat(trace->getRNG(),0.0,w);
  double L = x0 - u;
  double R = x0 + (w - u);

  // Expand the interval
  int J = floor(gsl_ran_flat(trace->getRNG(),0.0,m));
  int K = (m - 1) - J;

  while (J > 0)
  {
    if (L <= lower) { break; }
    double logd = computeLogDensity(L);
    // cout << "Expanding down from L " << L << " logd " << logd << " logy " << logy << endl;
    if (logd <= logy) { break; }
    if (logd != logd) { break; } // Poor man's NaN test
    L -= w;
    J -= 1;
  }

  while (K > 0)
  {
    if (R >= upper) { break; }
    double logd = computeLogDensity(R);
    // cout << "Expanding up from R " << R << " logd " << logd << " logy " << logy << endl;
    if (logd <= logy) { break; }
    if (logd != logd) { break; } // Poor man's NaN test
    R += w;
    K -= 1;
  }

  /* Shrink interval to lower and upper bounds */
  if (L < lower) { L = lower; }
  if (R > upper) { R = upper; }

  /* Sample from the interval, shrinking on rejections */
  while (true)
  {
    double x1 = gsl_ran_flat(trace->getRNG(),L,R);
    double gx1 = computeLogDensity(x1);
    // cout << "Slicing at x1 " << x1 << " gx1 " << gx1 << " logy " << logy << " L " << L << " R " << R << endl;

    if (gx1 >= logy) { return x1; }
    if (x1 > x0) { R = x1; }
    else { L = x1; }
  }
}

pair<Trace*,double> SliceGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;

  seed = time(NULL);

  assertTrace(trace,scaffold);
  assert(scaffold->border.size() == 1);

  pnode = dynamic_cast<ApplicationNode*>(scaffold->getPrincipalNode()); // todo have scaffold return an app node
  psp = trace->getPSP(pnode);

  assert(psp->isContinuous());

  VentureValuePtr currentVValue = trace->getValue(pnode);
  double x0 = currentVValue->getDouble();

  trace->registerLKernel(scaffold,pnode,shared_ptr<LKernel>(new DeterministicLKernel(currentVValue,psp)));
  pair<double, shared_ptr<DB> > rhoWeightAndDB = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = rhoWeightAndDB.first;
  rhoDB = rhoWeightAndDB.second;
  assertTorus(scaffold);

  double rhoLD = computeLogDensity(x0);
  double w = 1; // TODO let psp's override this
  int m = 1000000; // TODO arbitrary large

  double lower = psp->getSupportLowerBound();
  double upper = psp->getSupportUpperBound();

  double x1 = sliceSample(x0,w,m,lower,upper);
  double xiLD = computeLogDensity(x1);
  trace->registerLKernel(scaffold,pnode,shared_ptr<LKernel>(new DeterministicLKernel(VentureValuePtr(new VentureNumber(x1)),psp)));
  double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),shared_ptr<map<Node*,Gradient> >());
  /* This is subtle. We cancel out the weight compensation that we got by "forcing" x1, so that the weight is as if it had been sampled.
     This is because this weight is cancelled elsewhere (in the mixing over the slice). */

  return make_pair(trace,(xiWeight - xiLD) - (rhoWeight - rhoLD));
}


void SliceGKernel::accept()
{

}


void SliceGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}

