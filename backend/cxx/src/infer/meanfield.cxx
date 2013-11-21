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
  trace->setOptions(false,nullptr);
  double weightXi = trace->regen(scaffold->border,scaffold,nullptr);
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
  trace->setOptions(false,xiDB);
  trace->detach(scaffold->border,scaffold);
  check.checkTorus(scaffold);
  trace->setOptions(true,rhoDB);
  trace->regen(scaffold->border,scaffold,nullptr);
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

  rhoDB = new OmegaDB;
  trace->setOptions(false,rhoDB);
  trace->detach(scaffold->border,scaffold);
  check.checkTorus(scaffold);

  for (size_t i = 0; i < numIters; ++i)
  {
    map<Node *, vector<double> > gradients;

    // Regen populates the gradients
    trace->setOptions(false,nullptr);
    double gain = trace->regen(scaffold->border,scaffold,&gradients);

    OmegaDB * detachedDB = new OmegaDB;
    trace->setOptions(false,detachedDB);
    trace->detach(scaffold->border,scaffold);
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
  trace->setOptions(false,nullptr);
  trace->regen(scaffold->border,scaffold,nullptr);
  OmegaDB * rhoDB2 = new OmegaDB;
  trace->setOptions(false,rhoDB2);
  weightRho = trace->detach(scaffold->border,scaffold);
  flushDB(rhoDB2,true);
  check.checkTorus(scaffold);
}
 
