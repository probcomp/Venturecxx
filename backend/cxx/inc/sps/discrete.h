#ifndef DISCRETE_SPS_H
#define DISCRETE_SPS_H

#include "sp.h"

struct BernoulliSP : SP
{ 
  BernoulliSP()
    { 
      isRandomOutput = true; 
      canAbsorbOutput = true;
      canEnumerateOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
  vector<VentureValue*> enumerateOutput(Node * node) const override;
};

struct CategoricalSP : SP
{ 
  CategoricalSP()
    { 
      isRandomOutput = true; 
      canAbsorbOutput = true;
      canEnumerateOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
  vector<VentureValue*> enumerateOutput(Node * node) const override;
};

struct UniformDiscreteSP : SP
{ 
  UniformDiscreteSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
      canEnumerateOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
  vector<VentureValue*> enumerateOutput(Node * node) const override;
};

struct PoissonSP : SP
{ 
  PoissonSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 

};

#endif
