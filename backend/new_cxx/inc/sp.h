#ifndef SP_H
#define SP_H

#include "types.h"
#include "value.h"
#include <map>

#include <gsl/gsl_rng.h>

struct SPAux;
struct LSR;
struct LatentDB;
struct PSP;
struct ApplicationNode;
struct RequestNode;
struct OutputNode;
struct Args;

struct VentureSPRef : VentureValue
{
  VentureSPRef(Node * makerNode): makerNode(makerNode) {}
  boost::python::dict toPython() const;
  Node * makerNode;
};

struct SPFamilies
{
  SPFamilies() {}
  SPFamilies(const VentureValuePtrMap<RootOfFamily> & families): families(families) {}

  VentureValuePtrMap<RootOfFamily> families;
  bool containsFamily(FamilyID id);
  RootOfFamily getRootOfFamily(FamilyID id);
  void registerFamily(FamilyID id,RootOfFamily root);
  void unregisterFamily(FamilyID id);
};

struct SPAux
{
  virtual ~SPAux() {}
//  virtual shared_ptr<SPAux> copy() const;
};

struct SP : VentureValue
{
  SP(PSP * requestPSP, PSP * outputPSP);
  
  shared_ptr<PSP> requestPSP;
  shared_ptr<PSP> outputPSP;
  
  virtual shared_ptr<PSP> getPSP(ApplicationNode * node) const;

  virtual shared_ptr<LatentDB> constructLatentDB() const;
  virtual double simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const;
  virtual double detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const;
  virtual bool hasAEKernel() const { return false; }
  virtual void AEInfer(shared_ptr<Args> args, gsl_rng * rng) const;
};

#endif
