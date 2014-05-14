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

shared_ptr<map<Node*,Gradient> > nullGradients;

void doGibbs(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold, vector<ApplicationNode*>& applicationNodes, size_t i, vector<vector<VentureValuePtr> >& valueTuples, shared_ptr<Particle>* particles, vector<double>& xiWeights)
{
  shared_ptr<Particle> particle(new Particle(trace));
  registerDeterministicLKernels(particle.get(), scaffold, applicationNodes, valueTuples[i]);
  
  particles[i] = particle;
  xiWeights[i] = regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
}

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
  vector<VentureValuePtr> currentValues;

  vector<vector<VentureValuePtr> > possibleValues;
  BOOST_FOREACH(ApplicationNode * node, applicationNodes)
  {
    currentValues.push_back(trace->getValue(node));
    
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
  shared_ptr<Particle>* particles = new shared_ptr<Particle>[numValues];
  vector<double> xiWeights(numValues, 0);
  vector<boost::thread*> threads;
  
  for (size_t i = 0; i < numValues; ++i)
  {
    threads.push_back(new boost::thread(doGibbs, trace, scaffold, applicationNodes, i, valueTuples, particles, xiWeights));
    //doGibbs(trace, scaffold, applicationNodes, i, valueTuples, particles, xiWeights);
  }
  
  for (size_t i = 0; i < threads.size(); ++i)
  {
    threads[i]->join();
    delete threads[i];
  }
  
  // sample exactly from the posterior
  size_t finalIndex = sampleCategorical(mapExpUptoMultConstant(xiWeights), trace->getRNG());
  finalParticle = particles[finalIndex];
  
  delete [] particles;

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
