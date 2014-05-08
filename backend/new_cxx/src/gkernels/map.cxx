#include "gkernels/map.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"
#include <ctime>

using std::function;
using std::pair;

MAPGKernel::MAPGKernel() 
:rng(gsl_rng_alloc(gsl_rng_mt19937)), seed(time(NULL)) {
  gsl_rng_set(rng.get(),seed);
}

pair<Trace*,double> MAPGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  /* detach and extract */
  registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = p.first;
  rhoDB = p.second;
  assertTorus(scaffold);
  // get principle nodes as application nodes.
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    assert(applicationNode);
    assert(!scaffold->isResampling(applicationNode->operatorNode));
    applicationNodes.push_back(applicationNode);
  }
  vector<VentureValuePtr> currentValues;
  // get current values of application nodes.
  vector<vector<VentureValuePtr> > possibleValues;
  BOOST_FOREACH(ApplicationNode * node, applicationNodes)
  {
    currentValues.push_back(trace->getValue(node));
  }
  /* evolve */
  vector<double> momenta = this.sampleMomenta(currentValues);
  double start_K = this.kinetic(momenta);
  GradientPotential grad_u = this.gradientOfRegen(trace, scaffold);
  // FIXME: save gradient.
  // vector<Gradient> start_grad_pot = [rhoDB.getPartial()]
  pair<vector<double>, double> particle = this.evolve(grad_u, currentValues, start_grad_pot, momenta);
  const vector<double>& proposedValues = particle.first;
  const double end_K = particle.second;
  registerDeterministicLKernels(trace, scaffold, applicationNodes, proposedValues);
  // double xiWeight = grad.fixed_regen(proposed_values) # Mutates the trace

  /* regen and attach */
  registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,rhoDB,shared_ptr<map<Node*,Gradient> >());

  return make_pair(trace,xiWeight - rhoWeight + start_K - end_K);
}

vector<double> MAPGKernel::sampleMomenta(vector<VentureValuePtr> currentValues)  {
  vetor<double> momenta;
  for(VentureValuePtr value : currentValues) {
    momenta.append(value.getDouble());
  }
  return momenta;
}

double MAPGKernel::kinectic(const vector<double>& momenta) const {
  double kin = 0;
  for(const double& m : momenta) {
    kin += m*m;
  }
  return kin*0.5;
}

GradientPotential 
MAPGKernel::gradientOfRegen(ConcreteTrace* trace, shared_ptr<Scaffold> scaffold) {
  return [](const vector<double>& values) {
    vector<double> gradient;
    return gradient;
  };
}


void MAPGKernel::accept() { }


void MAPGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
