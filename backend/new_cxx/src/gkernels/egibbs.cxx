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
#include <math.h>
#include <boost/foreach.hpp>

void registerDeterministicLKernels(ConcreteTrace * trace,
  shared_ptr<Scaffold> scaffold,
  const vector<OutputNode*>& outputNodes,
  const vector<VentureValuePtr>& values)
{
  for (size_t i = 0; i < outputNodes.size(); ++i)
  {
    scaffold->lkernels[outputNodes[i]] =
      shared_ptr<DeterministicLKernel>(new DeterministicLKernel(values[i], trace->getPSP(outputNodes[i])));
  }
}

pair<Trace*,double> EnumerativeGibbsGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  
  assertTrace(trace,scaffold);
  assert(scaffold->border.size() == 1);
  
  // principal nodes should be ApplicationNodes
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<OutputNode*> outputNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    OutputNode * outputNode = dynamic_cast<OutputNode*>(node);
    assert(outputNode);
    assert(!scaffold->isResampling(outputNode->operatorNode));
    outputNodes.push_back(outputNode);
  }
  
  // compute the cartesian product of all possible values
  vector<VentureValuePtr> currentValues;
  vector<vector<VentureValuePtr> > possibleValues;
  BOOST_FOREACH(OutputNode * node, outputNodes)
  {
    currentValues.push_back(trace->getValue(node));
    
    shared_ptr<PSP> psp = trace->getPSP(node);
    
    shared_ptr<Args> args = trace->getArgs(node);
    assert(psp->canEnumerateValues(args));
    
    possibleValues.push_back(psp->enumerateValues(args));
  }
  vector<vector<VentureValuePtr> > valueTuples = cartesianProduct(possibleValues);
  
  // detach and extract from the principal nodes
  registerDeterministicLKernels(trace, scaffold, outputNodes, currentValues);
  pair<double, shared_ptr<DB> > rhoWeightAndDB = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = rhoWeightAndDB.first;
  rhoDB = rhoWeightAndDB.second;
  assertTorus(scaffold);
  
  shared_ptr<map<Node*,Gradient> > nullGradients;
  
  // regen all possible values
  vector<shared_ptr<Particle> > particles;
  vector<double> xiWeights;
  BOOST_FOREACH(vector<VentureValuePtr> valueTuple, valueTuples)
  {
    // TODO skip currentValues
    if (VentureValuePtr(new VentureArray(valueTuple))->equals(VentureValuePtr(new VentureArray(currentValues)))) { continue; }
    registerDeterministicLKernels(trace, scaffold, outputNodes, valueTuple);
    shared_ptr<Particle> particle(new Particle(trace));
    particles.push_back(particle);
    
    double xiWeight =
      regenAndAttach(particle.get(),scaffold->border[0],scaffold,false,shared_ptr<DB>(new DB()),nullGradients);
    xiWeights.push_back(xiWeight);
  }
  
  // sample a new particle
  size_t finalIndex = sampleCategorical(mapExp(xiWeights), trace->getRNG());
  finalParticle = particles[finalIndex];
  
  // compute the acceptance ratio
  vector<double> otherXiWeightsWithRho = xiWeights;
  otherXiWeightsWithRho.erase(otherXiWeightsWithRho.begin() + finalIndex);
  otherXiWeightsWithRho.push_back(rhoWeight);

  double weightMinusXi = logaddexp(otherXiWeightsWithRho);
  double weightMinusRho = logaddexp(xiWeights);
  double alpha = weightMinusRho - weightMinusXi;
  
  return make_pair(finalParticle.get(),alpha);
}

void EnumerativeGibbsGKernel::accept()
{
  finalParticle->commit();
  // assertTrace(self.trace,self.scaffold)    
}

void EnumerativeGibbsGKernel::reject()
{
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
  // assertTrace(self.trace,self.scaffold)
}
