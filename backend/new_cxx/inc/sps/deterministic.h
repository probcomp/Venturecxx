#ifndef DETERMINISTIC_PSPS_H
#define DETERMINISTIC_PSPS_H

#include "psp.h"
#include "args.h"

struct PlusOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct MinusOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct TimesOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct DivOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct EqOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct GtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct GteOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct LtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct LteOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct SinOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct CosOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct TanOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct HypotOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct ExpOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct LogOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct PowOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct SqrtOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct NotOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};

struct IsSymbolOutputPSP : PSP
{ 
  VentureValuePtr simulate(shared_ptr<Args> args, gsl_rng * rng) const override;
};


#endif
