#ifndef GKERNEL_H
#define GKERNEL_H

#include "types.h"

struct Scaffold;
struct ConcreteTrace;
struct Trace;

struct GKernel
{
  virtual pair<Trace*,double> propose(ConcreteTrace * trace,
				      shared_ptr<Scaffold> scaffold) =0;

  virtual void accept() =0;
  virtual void reject() =0;
  
};


#endif
