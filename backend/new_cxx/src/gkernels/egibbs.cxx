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

  // detach and extract from the principal nodes
  registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  pair<double, shared_ptr<DB> > rhoWeightAndDB = detachAndExtract(trace,scaffold->border[0],scaffold);
  //double rhoWeight = rhoWeightAndDB.first;
  rhoDB = rhoWeightAndDB.second;
  assertTorus(scaffold);
  
  shared_ptr<map<Node*,Gradient> > nullGradients;
  
  // regen all possible values
  vector<shared_ptr<Particle> > particles;
  vector<double> xiWeights;

  BOOST_FOREACH(vector<VentureValuePtr> valueTuple, valueTuples)
  {
    shared_ptr<Particle> particle(new Particle(trace));
    registerDeterministicLKernels(particle.get(), scaffold, applicationNodes, valueTuple);
    particles.push_back(particle);
    
    double xiWeight =
      regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
    xiWeights.push_back(xiWeight);
  }
  
  // sample exactly from the posterior
  size_t finalIndex = sampleCategorical(mapExpUptoMultConstant(xiWeights), trace->getRNG());
  finalParticle = particles[finalIndex];

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
