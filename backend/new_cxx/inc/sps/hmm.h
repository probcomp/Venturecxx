#ifndef SPS_HMM_H
#define SPS_HMM_H

#include "Eigen/Dense"
#include "srs.h"
#include "psp.h"
#include "sp.h"
#include "db.h"

using Eigen::MatrixXd;
using Eigen::VectorXd;

struct HMMSPAux : SPAux
{
  /* Latents */
  vector<VectorXd> xs; 
  
  /* Observations: may be many observations at a single index */
  /* We expect very few, otherwise we would use a set */
  map<size_t,vector<uint32_t> > os;

  SPAux* copy_help(ForwardingMap* m) const;

};

struct HMMLSR : LSR
{ 
  HMMLSR(uint32_t index): index(index) {}
  uint32_t index; 
};

struct HMMLatentDB : LatentDB
{
  map<size_t,MatrixXd> xs; 
};


struct MakeUncollapsedHMMOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
};


struct UncollapsedHMMSP : SP
{
  UncollapsedHMMSP(PSP * requestPSP, PSP * outputPSP,MatrixXd p0,MatrixXd T,MatrixXd O);
  shared_ptr<LatentDB> constructLatentDB() const;
  double simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const;
  double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  bool hasAEKernel() const { return true; }
  void AEInfer(shared_ptr<SPAux> spAux, shared_ptr<Args> args, gsl_rng * rng) const;

  const MatrixXd p0;
  const MatrixXd T;
  const MatrixXd O;
};


struct UncollapsedHMMOutputPSP : RandomPSP
{
  UncollapsedHMMOutputPSP(MatrixXd O);
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;

  const MatrixXd O;
};

struct UncollapsedHMMRequestPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
};



#endif
