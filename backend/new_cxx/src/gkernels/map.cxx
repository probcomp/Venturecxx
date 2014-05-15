#include "gkernels/map.h"
#include "gkernels/hmc.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "node.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"
#include <ctime>

#include <boost/foreach.hpp>

using std::function;
using std::pair;

MAPGKernel::MAPGKernel(double epsilon, int steps)  
:epsilon(new VentureNumber(epsilon)), steps(new VentureNumber(steps)) {
}

pair<Trace*,double> MAPGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  set<Node*> pNodes = scaffold->getPrincipalNodes();
  vector<ApplicationNode*> applicationNodes;
  BOOST_FOREACH(Node * node, pNodes)
  {
    ApplicationNode * applicationNode = dynamic_cast<ApplicationNode*>(node);
    applicationNodes.push_back(applicationNode);
    // cout << "old node " << node << endl;
  }
  // cout << "num pnodes " << applicationNodes.size() << endl;
  vector<VentureValuePtr> currentValues = trace->getCurrentValues(pNodes);
  // cout << "current values " << toString(currentValues);
  /* detach and extract */
  registerDeterministicLKernels(trace, scaffold, applicationNodes, currentValues);
  double rhoWeight = this->prepare(trace, scaffold, true);
  GradientOfRegen grad(trace, scaffold);
  vector<VentureValuePtr> start_grad;
  // cout << "start_grad" << toString(start_grad);
  BOOST_FOREACH(Node * pNode, pNodes) {
    start_grad.push_back(this->rhoDB->getPartial(pNode));
  }
  vector<VentureValuePtr> proposed = this->evolve(grad, currentValues, start_grad);
  registerDeterministicLKernels(trace, scaffold, applicationNodes, proposed);
  cout << "proposed " << toString(proposed) << endl;
  double xiWeight = grad.fixed_regen(proposed);
  return make_pair(trace, 1000); // force accept. 
}

vector<VentureValuePtr> MAPGKernel::evolve(GradientOfRegen& grad, vector<VentureValuePtr>& currentValues, const vector<VentureValuePtr>& start_grad) {
  shared_ptr<VentureArray> xs(new VentureArray(currentValues));
  shared_ptr<VentureArray> dxs(new VentureArray(start_grad));
  for(int i = 0; i < this->steps->getInt(); i++) {
    xs = dynamic_pointer_cast<VentureArray>(xs+dxs*this->epsilon);
    assert(xs != NULL);
    dxs = shared_ptr<VentureArray>(new VentureArray(grad(xs->getArray())));
    // cout << "gradient " << toString(dxs) << endl;
    // cout << "xs " << toString(xs) << endl;
    // cout << "dxs*epsilon" << toString(dxs*this->epsilon) << endl;
    // cout << "xs+dxs*epsilon" << toString(xs+dxs*this->epsilon) << endl;
    assert(dxs != NULL);
  }
  return xs->getArray();
}


void MAPGKernel::accept() { }


void MAPGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
