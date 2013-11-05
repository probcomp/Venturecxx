#include "value.h"
#include "utils.h"
#include "sps/stathelpers.h"
#include "node.h"
#include "sp.h"
#include "sps/makesymdirmult.h"
#include "sps/makeucsymdirmult.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>


VentureValue * MakeUCSymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureAtom * n = dynamic_cast<VentureAtom *>(operands[1]->getValue());

  assert(alpha);
  assert(n);


  double *alphaVector = new double[n->n];
  for (size_t i = 0; i < n->n; ++i) 
  { 
    alphaVector[i] = alpha->x;
  }

  /* TODO GC watch the NEW */
  double *theta = new double[n->n];

  gsl_ran_dirichlet(rng,n->n,alphaVector,theta);

  delete[] alphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,n->n));
}

double MakeUCSymDirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureAtom * n = dynamic_cast<VentureAtom *>(operands[1]->getValue());
  VentureSP * vsp = dynamic_cast<VentureSP *>(value);
  assert(alpha);
  assert(n);
  assert(vsp);

  double *alphaVector = new double[n->n];
  for (size_t i = 0; i < n->n; ++i) { alphaVector[i] = alpha->x; }

  UCSymDirMultSP * sp = dynamic_cast<UCSymDirMultSP *>(vsp->sp);

  double ld = gsl_ran_dirichlet_lnpdf(n->n,alphaVector,sp->theta);
  delete[] alphaVector;
  return ld;
}

VentureValue * MakeUCSymDirMultAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng)
{

  vector<Node *> & operands = appNode->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureAtom * n = dynamic_cast<VentureAtom *>(operands[1]->getValue());

  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(appNode->madeSPAux);

  assert(alpha);
  assert(n);
  assert(spaux);

  double *conjAlphaVector = new double[n->n];
  for (size_t i = 0; i < n->n; ++i) 
  { 
    conjAlphaVector[i] = alpha->x + spaux->counts[i];
  }

  /* TODO GC watch the NEW */
  double *theta = new double[n->n];

  gsl_ran_dirichlet(rng,n->n,conjAlphaVector,theta);

  delete[] conjAlphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,n->n));
}

double MakeUCSymDirMultAAAKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  return 0;
}

double UCSymDirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(generic_spaux);
  assert(spaux);

  return gsl_ran_multinomial_lnpdf(n,theta,&(spaux->counts[0]));
}

VentureValue * UCSymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < n; ++i)
  {
    sum += theta[i];
    if (u < sum) { return new VentureAtom(i); }
  }
  assert(false);
  return nullptr;
}  


double UCSymDirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  return theta[observedIndex];
}

void UCSymDirMultSP::incorporateOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void UCSymDirMultSP::removeOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * UCSymDirMultSP::constructSPAux() const
{
  return new SymDirMultSPAux(n);
}

void UCSymDirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}



