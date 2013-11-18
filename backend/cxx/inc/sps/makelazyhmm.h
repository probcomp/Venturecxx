#ifndef MAKE_LAZY_HMM_H
#define MAKE_LAZY_HMM_H

#include "Eigen/Dense"

#include "sp.h"
#include "spaux.h"
#include "omegadb.h"
#include "lkernel.h"
#include "srs.h"
#include <vector>
#include <string>

using namespace Eigen;

struct HMM_HSR : HSR 
{ 
  HMM_HSR(uint32_t index): index(index) {}
  uint32_t index; 
};

struct LazyHMMSPAux : SPAux
{
  LazyHMMSPAux * clone() const override; // TODO implement
  /* Latents */
  vector<VectorXd> xs; 
  
  /* Observations: may be many observations at a single index */
  /* We expect very few, otherwise we would use a set */
  map<size_t,vector<uint32_t> > os;
};

/* Used for detachAll/simulateAll */
struct LazyHMMLatentDBAll : LatentDB
{
  vector<VectorXd> xs; 
};

/* Used for detach/simulate */
struct LazyHMMLatentDBSome : LatentDB
{
  map<size_t,VectorXd> xs; 
};


struct MakeLazyHMMAAAKernel : LKernel
{
  /* Generates a LazyHMMSP, and then proposes to all of the latents by 
     forwards-filtering/backwards-sampling. */
  VentureValue * simulate(VentureValue * oldVal, const Args & args, gsl_rng * rng) override;
};


struct MakeLazyHMMSP : SP
{
  MakeLazyHMMSP()
    {
      isRandomOutput = true;
      childrenCanAAA = true;
    }

  /* Generaters a LazyHMMSP */
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;

  /* For the child. */
  double detachAllLatents(SPAux * spaux) const;

  LKernel * getAAAKernel() const override { return new MakeLazyHMMAAAKernel; }
};


struct LazyHMMSP : SP
{
  LazyHMMSP(const VectorXd & p0, const MatrixXd & T, const MatrixXd & O): 
    p0(p0), T(T), O(O)
    {
      tracksSamples = true;
      makesHSRs = true;
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  /* Simply applies O to appropriate latent and then samples from it.*/
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  double logDensityOutput(VentureValue * value, const Args & args) const override;

  VentureValue * simulateRequest(const Args & args, gsl_rng * rng) const override;


  /* SPAux */
  SPAux * constructSPAux() const;
  void destroySPAux(SPAux * spaux);

  /* Incorporate / Remove */
  void incorporateOutput(VentureValue * value, const Args & args) const override;
  void removeOutput(VentureValue * value, const Args & args) const override;

  /* (hmm n) will make the request "n", which may cause latents to be
     evaluated from the prior. */
  double simulateLatents(SPAux * spaux,
				 HSR * hsr,
				 gsl_rng * rng) const override;

  /* Some latents may be detached and put in the LatentDB if they are no
     longer required. */
  double detachLatents(SPAux * spaux,
		       HSR * hsr) const;

  

  VectorXd p0;
  MatrixXd T;
  MatrixXd O;
};



#endif
