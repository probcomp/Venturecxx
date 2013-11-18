#include "value.h"
#include "utils.h"
#include "node.h"
#include "sp.h"
#include "sps/makesymdirmult.h"
#include "sps/makeucsymdirmult.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>


VentureValue * MakeUCSymDirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * n = dynamic_cast<VentureNumber *>(args.operands[1]);

  assert(alpha);
  assert(n);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) 
  { 
    alphaVector[i] = alpha->x;
  }

  /* TODO GC watch the NEW */
  double *theta = new double[d];

  gsl_ran_dirichlet(rng,d,alphaVector,theta);

  delete[] alphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,d));
}

double MakeUCSymDirMultSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * n = dynamic_cast<VentureNumber *>(args.operands[1]);
  VentureSP * vsp = dynamic_cast<VentureSP *>(value);
  assert(alpha);
  assert(n);
  assert(vsp);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) { alphaVector[i] = alpha->x; }

  UCSymDirMultSP * sp = dynamic_cast<UCSymDirMultSP *>(vsp->sp);

  double ld = gsl_ran_dirichlet_lnpdf(d,alphaVector,sp->theta);
  delete[] alphaVector;
  return ld;
}

VentureValue * MakeUCSymDirMultAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng)
{

  VentureNumber * alpha = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * n = dynamic_cast<VentureNumber *>(args.operands[1]);

  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(appNode->madeSPAux);

  assert(alpha);
  assert(n);
  assert(spaux);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *conjAlphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) 
  { 
    conjAlphaVector[i] = alpha->x + spaux->counts[i];
  }

  /* TODO GC watch the NEW */
  double *theta = new double[d];

  gsl_ran_dirichlet(rng,d,conjAlphaVector,theta);

  delete[] conjAlphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,d));
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

VentureValue * UCSymDirMultSP::simulateOutput(const Args & args, gsl_rng * rng) const
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


double UCSymDirMultSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  return theta[observedIndex];
}

void UCSymDirMultSP::incorporateOutput(VentureValue * value, const Args & args) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void UCSymDirMultSP::removeOutput(VentureValue * value, const Args & args) const
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



