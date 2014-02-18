#ifndef SPS_HMM_H
#define SPS_HMM_H

struct HMMSPAux : SPAux
{
  /* Latents */
  vector<VectorXd> xs; 
  
  /* Observations: may be many observations at a single index */
  /* We expect very few, otherwise we would use a set */
  map<size_t,vector<uint32_t> > os;
};


struct MakeUncollapsedHMMOutputPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
};


struct UncollapsedHMMSP : SP
{
  UncollapsedHMMSP();
  shared_ptr<LatentDB> constructLatentDB() const;
  void simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const;
  double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  bool hasAEKernel() const { return false; }
  void AEInfer(shared_ptr<Args> args, gsl_rng * rng) const;
};


struct UncollapsedHMMOutputPSP : RandomPSP
{
  UncollapsedHMMOutputPSP();
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
  double logDensity(VentureValuePtr value,shared_ptr<Args> args) const;
  void incorporate(VentureValuePtr value,shared_ptr<Args> args) const;
  void unincorporate(VentureValuePtr value,shared_ptr<Args> args) const;
};

struct UncollapsedHMMRequestPSP : PSP
{
  VentureValuePtr simulate(shared_ptr<Args> args,gsl_rng * rng) const;
};



#endif
