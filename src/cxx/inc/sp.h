#ifndef SP_H
#define SP_H

#include "address.h"
#include "spaux.h"
#include "srs.h"
#include "value.h"
#include "value_types.h"

#include <iostream>
#include <gsl/gsl_rng.h>

struct Node;
struct LatentDB;

enum class NodeType;

/* Although this is not technically an abstract class, 
   one cannot have both simulate defaults at the same time,
   so it should be considered an abstract class. */
struct SP
{
  SP(std::string s): address(s) {}
  SP(const Address &a): address(a) {}

  /* Simulate */
  VentureValue * simulate(Node * node, gsl_rng * rng);
  virtual VentureValue * simulateRequest(Node * node, gsl_rng * rng) { return new VentureRequest; }
  virtual VentureValue * simulateOutput(Node * node, gsl_rng * rng) { return nullptr; };

  /* LogDensity */
  double logDensity(VentureValue * value, Node * node);
  virtual double logDensityRequest(VentureValue * value, Node * node) { return 0; }
  virtual double logDensityOutput(VentureValue * value, Node * node) { return 0; }

  /* Incorporate */
  void incorporate(VentureValue * value, Node * node);
  virtual void incorporateRequest(VentureValue * value, Node * node) { }
  virtual void incorporateOutput(VentureValue * value, Node * node) { }

  /* Remove */
  void remove(VentureValue * value, Node * node);
  virtual void removeRequest(VentureValue * value, Node * node) {}
  virtual void removeOutput(VentureValue * value, Node * node) {}

  /* Can Absorb */
  bool canAbsorb(NodeType nodeType);
  bool canAbsorbRequest{true};
  bool canAbsorbOutput{false};

  /* Is Random w MH proposal */
  bool isRandom(NodeType nodeType);
  bool isRandomRequest{false};
  bool isRandomOutput{false};

  /* LatentDBs */
  virtual LatentDB * constructLatentDB() const { return nullptr; }
  virtual void destroyLatentDB() const { }

  /* ESRs */
  virtual bool hasLatents() { return false; }
  virtual double simulateLatents(SPAux * spAux,
				 ESR * esr,
				 bool shouldRestore,
				 LatentDB * latentDB,
				 gsl_rng * rng) const { return 0; }

  virtual double detachLatents(SPAux * spAux,
			       ESR * esr,
			       LatentDB * latentDB) const { return 0; }

  virtual LatentDB * detachAllLatents(SPAux * spaux) const { return nullptr; }
  virtual void restoreAllLatents(SPAux * spaux, LatentDB * latentDB) {};

  Address address;

  bool isCSRReference{false};
  bool childrenCanAAA{false};
  bool hasAEKernel{false};

  virtual ~SP() {};


};



#endif
