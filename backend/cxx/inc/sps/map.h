#ifndef MAP_SPS_H
#define MAP_SPS_H

#include "sp.h"

struct MakeMapSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct MapContainsSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct MapLookupSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};


#endif
