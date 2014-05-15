#include "gkernels/hmc.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "node.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"
#include <ctime>

#include <boost/foreach.hpp>
#include <boost/assign/list_of.hpp>

using std::function;
using std::pair;

HMCGKernel::HMCGKernel(double epsilon, int steps) 
:rng(gsl_rng_alloc(gsl_rng_mt19937)), seed(time(NULL)), 
 epsilon(new VentureNumber(epsilon)), steps(new VentureNumber(steps)) {
  gsl_rng_set(rng,seed);
}

pair<Trace*,double> HMCGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  vector<Node*> allNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    applicationNodes.push_back(applicationNode);
    // cout << "old node " << node << endl;
    allNodes.push_back(node);
  }
  // cout << "num pnodes " << applicationNodes.size() << endl;
  vector<VentureValuePtr> currentValues = trace->getCurrentValues(pNodes);
  // cout << "current values " << toString(currentValues);
  /* detach and extract */
  registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  double rhoWeight = this->prepare(trace, scaffold, true);

  /* evolve */
  VentureValuePtr start_q = VentureArray::makeValue(currentValues);
  VentureValuePtr momenta = this->sampleMomenta(start_q);
  VentureValuePtr start_grad_pot = VentureArray::makeValue(this->rhoDB->getPartials(allNodes));

  double start_K = this->kinetic(momenta);
  GradientOfRegen grad(trace, scaffold);
  
  pair<VentureValuePtr, double> particle = this->evolve(grad, start_q, start_grad_pot, momenta);

  // cout << "new particle " << toString(particle.first->getArray()) << endl;
  double end_K = particle.second;
  VentureValuePtrVector proposed = particle.first->getArray();
  registerDeterministicLKernels(trace, scaffold, applicationNodes, proposed);
  
  double xiWeight = grad.fixed_regen(proposed) ;
  // cout << "proposed " << toString(proposed) << endl;  

  return make_pair(trace,xiWeight - rhoWeight + start_K - end_K);
}

VentureValuePtr HMCGKernel::sampleMomenta(VentureValuePtr currentValues) const {
  vector<VentureValuePtr> momenta;
  BOOST_FOREACH(VentureValuePtr value, currentValues->getArray()) {
    shared_ptr<VentureNumber> valueNumber = dynamic_pointer_cast<VentureNumber>(value);
    if(valueNumber != NULL) {
      momenta.push_back(VentureNumber::makeValue(gsl_ran_gaussian(rng, 1)));
      continue;
    }
    shared_ptr<VentureVector> valueVector = dynamic_pointer_cast<VentureVector>(value);
    if(valueVector != NULL) {
      VectorXd momentVector(valueVector->v.size());
      for(int si = 0; si < valueVector->v.size(); si++) momentVector[si] = gsl_ran_gaussian(rng, 1);
      momenta.push_back(VentureVector::makeValue(momentVector));      
      continue;
    }
  }
  return VentureArray::makeValue(momenta);
}

double HMCGKernel::kinetic(const VentureValuePtr momenta) const {
  double kin = 0;
  BOOST_FOREACH(const VentureValuePtr m, momenta->getArray()) {
    shared_ptr<VentureNumber> valueNumber = dynamic_pointer_cast<VentureNumber>(m);
    if(valueNumber != NULL) {
      kin += m->getDouble()*m->getDouble();
      continue;
    }
    shared_ptr<VentureVector> valueVector = dynamic_pointer_cast<VentureVector>(m);
    if(valueVector != NULL) {
      for(int si = 0; si < valueVector->v.size(); si++) kin += valueVector->v[si]*valueVector->v[si];
      continue;
    }
  }
  return kin*0.5;
}


pair<VentureValuePtr, double> 
HMCGKernel::evolve(GradientOfRegen& grad, const VentureValuePtr& start_q, const VentureValuePtr& start_grad_q, 
                      const VentureValuePtr& start_p) {
  // int numSteps = int(gsl_rng_uniform(rng)*steps->getDouble())+1;
  int numSteps = steps->getDouble();
  // cout << "num steps " << numSteps << endl;
  const VentureValuePtr half = VentureNumber::makeValue(epsilon->getDouble()*.5);
  VentureValuePtr q = start_q;
  VentureValuePtr dpdt = start_grad_q;
  // cout << "start p = " << toString(start_p) << endl;
  // cout << "grad = " << toString(start_grad_q) << endl;
  // cout << "half = " << toString(half) << endl;
  // cout << "grad*half = " << toString(start_grad_q*half) << endl;
  VentureValuePtr p = start_p-(start_grad_q*half);
  // cout << "grad*half = " << toString(start_grad_q*half) << endl;
  for(int si = 0; si < numSteps; si++) {
    q = q+p*epsilon;
    dpdt = VentureArray::makeValue(grad(q->getArray()));
    p = p-dpdt*epsilon;
    // cout << "2x" << endl;
  }
  p = p+dpdt*half;
  // Negate momenta at the end to make the proposal symmetric
  // (irrelevant if the kinetic energy function is symmetric)
  p = p->neg();
  return make_pair(q, kinetic(p));
}

void HMCGKernel::accept() { }


void HMCGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}



GradientOfRegen::GradientOfRegen(ConcreteTrace * trace, shared_ptr<Scaffold> scaffold) 
:trace(trace), scaffold(scaffold) {

}


VentureValuePtrVector GradientOfRegen::operator()(const VentureValuePtrVector& values) {
  this->fixed_regen(values);
  set<Node*> pNodes = this->scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    applicationNodes.push_back(applicationNode);
  }
  vector<set<Node* > > pNodeVec = boost::assign::list_of(pNodes);
  shared_ptr<Scaffold> new_scaffold = constructScaffold(this->trace, pNodeVec, false);
  registerDeterministicLKernels(trace, new_scaffold, applicationNodes, values); 
  pair<double,shared_ptr<DB> > p = detachAndExtract(trace,new_scaffold->border[0],new_scaffold,true);
  this->scaffold = new_scaffold;
  VentureValuePtrVector result;
  BOOST_FOREACH(Node * node, pNodes) {
    result.push_back(p.second->getPartial(node));
  }
  return result;
}

double GradientOfRegen::fixed_regen(const VentureValuePtrVector& values) {
  // should we save state of RNG?
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    applicationNodes.push_back(applicationNode);
  }
  registerDeterministicLKernels(trace, scaffold, applicationNodes, values);
  return regenAndAttach(trace, scaffold->border[0], scaffold, false, shared_ptr<DB>(new DB()), shared_ptr<map<Node*,Gradient> >());
}

