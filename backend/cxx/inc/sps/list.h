#ifndef LIST_SPS_H
#define LIST_SPS_H

#include "sp.h"

struct PairSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct FirstSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};

struct RestSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};

struct ListSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override;
};

struct IsPairSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};


struct ListRefSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};

struct MapListSP : SP
{
  MapListSP()
    {
      makesESRs = true;
      canAbsorbRequest = false;
    }
  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override;

};





#endif
