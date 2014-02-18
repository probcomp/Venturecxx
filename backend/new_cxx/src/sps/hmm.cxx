// struct HMMSPAux : SPAux
// {
//   /* Latents */
//   vector<VectorXd> xs; 
  
//   /* Observations: may be many observations at a single index */
//   /* We expect very few, otherwise we would use a set */
//   map<size_t,vector<uint32_t> > os;
// };

/* MakeUncollapsedHMMSP */

VentureValuePtr MakeUncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{ assert(false); }


/* UncollapsedHMMSP */
  UncollapsedHMMSP::UncollapsedHMMSP(){ assert(false); }
  shared_ptr<LatentDB> UncollapsedHMMSP::constructLatentDB() const { assert(false); }
  void UncollapsedHMMSP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB) const { assert(false); }
  double UncollapsedHMMSP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const { assert(false); }
  bool UncollapsedHMMSP::hasAEKernel() const { return true{ assert(false); } }
  void UncollapsedHMMSP::AEInfer(shared_ptr<Args> args, gsl_rng * rng) const { assert(false); }


/* UncollapsedHMMOutputPSP */

  UncollapsedHMMOutputPSP::UncollapsedHMMOutputPSP(){ assert(false); }
  VentureValuePtr UncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }
  double UncollapsedHMMOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }
  void UncollapsedHMMOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }
  void UncollapsedHMMOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }


/* UncollapsedHMMRequestPSP */

  VentureValuePtr UncollapsedHMMRequestPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }




#endif
