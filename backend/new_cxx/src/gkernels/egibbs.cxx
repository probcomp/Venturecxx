#include "gkernels/egibbs.h"
#include "detach.h"
#include "utils.h"
#include "particle.h"
#include "consistency.h"
#include "regen.h"
#include "db.h"
#include "concrete_trace.h"
#include "args.h"
#include "lkernel.h"
#include "gkernel.h"
#include <math.h>
#include <boost/foreach.hpp>
#include <boost/thread.hpp>

struct EGibbsWorker
{
  EGibbsWorker(ConcreteTrace * trace): trace(trace) {}
  void doEGibbs(shared_ptr<Scaffold> scaffold, vector<ApplicationNode*>& applicationNodes, vector<VentureValuePtr> & valueTuple)
  {
    particle = shared_ptr<Particle>(new Particle(trace));
    registerDeterministicLKernels(particle.get(), scaffold, applicationNodes, valueTuple);
    weight = regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
  }
  ConcreteTrace * trace;
  shared_ptr<map<Node*,Gradient> > nullGradients;
  shared_ptr<Particle> particle;
  double weight;
};

pair<Trace*,double> EnumerativeGibbsGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;

  assertTrace(trace,scaffold);
  assert(scaffold->border.size() == 1);

  // principal nodes should be ApplicationNodes
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    assert(applicationNode);
    assert(!scaffold->isResampling(applicationNode->operatorNode));
    applicationNodes.push_back(applicationNode);
  }

  // compute the cartesian product of all possible values
  vector<vector<VentureValuePtr> > possibleValues;
  BOOST_FOREACH(ApplicationNode * node, applicationNodes)
  {
    shared_ptr<PSP> psp = trace->getPSP(node);
    shared_ptr<Args> args = trace->getArgs(node);
    assert(psp->canEnumerateValues(args));
    possibleValues.push_back(psp->enumerateValues(args));
  }

  vector<vector<VentureValuePtr> > valueTuples = cartesianProduct(possibleValues);
  size_t numValues = valueTuples.size();

  // detach and extract from the principal nodes
  //registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);

  // regen all possible values
  vector<shared_ptr<Particle> > particles(numValues);
  vector<double> particleWeights(numValues);
  vector<shared_ptr<EGibbsWorker> > workers(numValues);
  if (inParallel)
  {
    vector<boost::thread*> threads(numValues);
    for (size_t p = 0; p < numValues; ++p)
    {
      workers[p] = shared_ptr<EGibbsWorker>(new EGibbsWorker(trace));
      boost::function<void()> th_func = boost::bind(&EGibbsWorker::doEGibbs,workers[p],scaffold,applicationNodes,valueTuples[p]);
      threads[p] = new boost::thread(th_func);
    }
    for (size_t p = 0; p < numValues; ++p)
    {
      threads[p]->join();
      particles[p] = workers[p]->particle;
      particleWeights[p] = workers[p]->weight;
      delete threads[p];
    }
  } else {
    for (size_t p = 0; p < numValues; ++p)
    {
      workers[p] = shared_ptr<EGibbsWorker>(new EGibbsWorker(trace));
      workers[p]->doEGibbs(scaffold,applicationNodes,valueTuples[p]);
      particles[p] = workers[p]->particle;
      particleWeights[p] = workers[p]->weight;
    }
  }

  finalParticle = selectParticle(particles, particleWeights, trace);
  return make_pair(finalParticle.get(),0);
}

void EnumerativeGibbsGKernel::accept()
{
  finalParticle->commit();
  // assertTrace(self.trace,self.scaffold)
}

void EnumerativeGibbsGKernel::reject()
{
  assert(false); // should never reject
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
  // assertTrace(self.trace,self.scaffold)
}

shared_ptr<Particle> EnumerativeGibbsGKernel::selectParticle(const vector<shared_ptr<Particle> >& particles,
                                                             const vector<double>& particleWeights,
                                                             ConcreteTrace* trace) const
{
  // sample exactly from the posterior
  size_t finalIndex = sampleCategorical(mapExpUptoMultConstant(particleWeights), trace->getRNG());
  return particles[finalIndex];
}

shared_ptr<Particle> EnumerativeMAPGKernel::selectParticle(const vector<shared_ptr<Particle> >& particles,
                                                           const vector<double>& particleWeights,
                                                           ConcreteTrace* trace) const
{
  // Deterministically choose the posterior maximum
  int max_i = -1;
  double max = -FLT_MAX;
  for (size_t i = 0; i < particleWeights.size(); i++)
  {
    if (particleWeights[i] > max) { max_i = i; max = particleWeights[i]; }
  }
  return particles[max_i];
}
