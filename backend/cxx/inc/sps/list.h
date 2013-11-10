#ifndef LIST_SPS_H
#define LIST_SPS_H

#include "sp.h"
#include "spaux.h"

struct VenturePair;

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



struct MapListSPAux : SPAux
{
  // TRUE indicates VentureSymbol
  // FALSE indicates VenturePair
  map<size_t, VenturePair *> ownedSymbols;
  map<size_t, VenturePair *> ownedPairs;
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
  void flushFamily(SPAux * spaux, size_t id) const override;
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override;
  SPAux * constructSPAux() const override { return new MapListSPAux; }

};





#endif
