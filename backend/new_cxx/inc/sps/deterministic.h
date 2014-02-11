#ifndef DETERMINISTIC_PSPS_H
#define DETERMINISTIC_PSPS_H

#include "sp.h"

struct PlusOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct MinusOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct TimesOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct DivOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct EqOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct GtOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct GteOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct LtOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct LteOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct SinOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct CosOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct TanOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct HypotOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct ExpOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct LogOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct PowOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct SqrtOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct NotOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};

struct IsSymbolOutputPSP : PSP
{ 
  VentureValuePtr simulateOutput(Args * args, gsl_rng * rng) const override;
};


#endif
