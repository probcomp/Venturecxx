#include "lkernel.h"
#include "infer/meanfield.h"
#include "trace.h"
#include "flush.h"
#include "check.h"
#include "node.h"
#include "value.h"
#include "scaffold.h"
#include "sp.h"


double MeanFieldGKernel::propose()
{
  /* Sample from the variational distribution. */
  double weightXi = trace->regen(scaffold->border,scaffold,false,nullptr,nullptr);
  return weightXi - weightRho;
}
 
void MeanFieldGKernel::accept()
{
  flushDB(rhoDB,false);
  rhoDB = nullptr;
}

void MeanFieldGKernel::reject()
{
  OmegaDB * xiDB = new OmegaDB;
  trace->detach(scaffold->border,scaffold,xiDB);
  check.checkTorus(scaffold);
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  flushDB(rhoDB,true);
  flushDB(xiDB,false);
  rhoDB = nullptr;
}

void MeanFieldGKernel::destroyParameters()
{
  delete scaffold;
}

bool MeanFieldGKernel::registerVariationalLKernels()
{
  bool hasVariational = false;
  for (pair<Node *, Scaffold::DRGNode> p : scaffold->drg)
  {
    Node * node = p.first;
    if (node->nodeType == NodeType::OUTPUT && 
	!scaffold->isResampling(node->operatorNode) &&
	node->sp()->hasVariationalLKernel)
    {
      scaffold->lkernels.insert({node,node->sp()->getVariationalLKernel(trace->getArgs(node))});
      hasVariational = true;
    }
  }
  return hasVariational;
}


void MeanFieldGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  delete sparam;

  /* Now, compute variational kernels through stochastic gradient descent. */
  double stepSize = 0.001;
  size_t numIters = 40;
  if (!registerVariationalLKernels()) { numIters = 0; }
  double rhoWeight;

  rhoDB = new OmegaDB;
  rhoWeight = trace->detach(scaffold->border,scaffold,rhoDB);
  check.checkTorus(scaffold);

  for (size_t i = 0; i < numIters; ++i)
  {
    map<Node *, vector<double> > gradients;

    // Regen populates the gradients
    double gain = trace->regen(scaffold->border,scaffold,false,nullptr,&gradients);

    OmegaDB * detachedDB = new OmegaDB;
    trace->detach(scaffold->border,scaffold,detachedDB);
    check.checkTorus(scaffold);
    flushDB(detachedDB,false);

    for (pair<Node *, LKernel*> p : scaffold->lkernels)
    {
      VariationalLKernel * vk = dynamic_cast<VariationalLKernel*>(p.second);
      if (vk) 
      { 
	assert(gradients.count(p.first));
	vk->updateParameters(gradients[p.first],gain,stepSize); 
      }
    }
  }
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  OmegaDB * rhoDB2 = new OmegaDB;
  weightRho = trace->detach(scaffold->border,scaffold,rhoDB2);
  flushDB(rhoDB2,true);
  check.checkTorus(scaffold);
}
 
