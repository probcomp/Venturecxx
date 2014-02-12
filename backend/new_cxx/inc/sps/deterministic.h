#ifndef DETERMINISTIC_PSPS_H
#define DETERMINISTIC_PSPS_H

#include "psp.h"
#include "args.h"

struct PlusOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct MinusOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct TimesOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct DivOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct EqOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct GtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct GteOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct LtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct LteOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct SinOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct CosOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct TanOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct HypotOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct ExpOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct LogOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct PowOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct SqrtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct NotOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};

struct IsSymbolOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const;
};


#endif
