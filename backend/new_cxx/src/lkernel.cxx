#include "lkernel.h"
#include "psp.h"
#include "sp.h"
#include "sprecord.h"

VentureValuePtr DefaultAAALKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) 
{ 
  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(makerPSP->simulate(args,rng));

  shared_ptr<VentureSPRecord> oldSPRecord = dynamic_pointer_cast<VentureSPRecord>(oldValue);
  assert(oldSPRecord);

  spRecord->spAux = oldSPRecord->spAux;
  return spRecord;
}

double DefaultAAALKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args) 
{ 
  shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(newValue);
  assert(spRecord);
  return spRecord->sp->outputPSP->logDensityOfCounts(spRecord->spAux);
}

VentureValuePtr DeterministicLKernel::simulate(Trace * trace,VentureValuePtr oldValue,shared_ptr<Args> args,gsl_rng * rng) 
{ 
  return value;
}

double DeterministicLKernel::weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,shared_ptr<Args> args)
{
  return psp->logDensity(newValue,args);
}
