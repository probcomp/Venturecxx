
#include "sp.h"
#include "sps/number.h"
#include "value.h"
#include <cassert>
#include <vector>
#include <math.h>

VentureValue * PlusSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  double sum = 0;
  for (size_t i = 0; i < args.operands.size(); ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber *>(args.operands[i]);
    assert(vdouble);
    sum += vdouble->x;
  }
  return new VentureNumber(sum);
}


VentureValue * MinusSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureNumber(d1->x - d2->x);
}

VentureValue * TimesSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  double prod = 1;
  for (size_t i = 0; i < args.operands.size(); ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber *>(args.operands[i]);
    assert(vdouble);
    prod *= vdouble->x;
  }
  return new VentureNumber(prod);
}

VentureValue * DivideSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
    VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
    VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
    assert(d1);
    assert(d2);
    return new VentureNumber(d1->x / d2->x);
}

VentureValue * PowerSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
    VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
    VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
    assert(d1);
    assert(d2);
    return new VentureNumber(pow(d1->x, d2->x));
}

VentureValue * EqualSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);

  if (d1 && d2) { return new VentureBool(d1->x == d2->x); }

  VentureBool * b1 = dynamic_cast<VentureBool *>(args.operands[0]);
  VentureBool * b2 = dynamic_cast<VentureBool *>(args.operands[1]);

  if (b1 && b2) { return new VentureBool(b1->pred == b2->pred); }

  VentureAtom * a1 = dynamic_cast<VentureAtom *>(args.operands[0]);
  VentureAtom * a2 = dynamic_cast<VentureAtom *>(args.operands[1]);

  if (a1 && a2) { return new VentureBool(a1->n == a2->n); }

  VentureSymbol * s1 = dynamic_cast<VentureSymbol *>(args.operands[0]);
  VentureSymbol * s2 = dynamic_cast<VentureSymbol *>(args.operands[1]);

  if (s1 && s2) { return new VentureBool(s1->sym == s2->sym); }

  return new VentureBool(false);
}

VentureValue * LessThanSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x < d2->x);
}

VentureValue * GreaterThanSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x > d2->x);
}

VentureValue * LessThanOrEqualToSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x <= d2->x);
}

VentureValue * GreaterThanOrEqualToSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->x >= d2->x);
}

VentureValue * RealSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureAtom * a = dynamic_cast<VentureAtom *>(args.operands[0]);
  assert(a);
  return new VentureNumber(a->n);
}

VentureValue * IntPlusSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  int sum = 0;
  for (size_t i = 0; i < args.operands.size(); ++i)
  {
    VentureNumber * vnum = dynamic_cast<VentureNumber *>(args.operands[i]);
    assert(vnum);
    sum += vnum->getInt();
  }
  return new VentureNumber(sum);
}

VentureValue * IntMinusSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureNumber(d1->getInt() - d2->getInt());
}

VentureValue * IntTimesSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  int prod = 1;
  for (size_t i = 0; i < args.operands.size(); ++i)
  {
    VentureNumber * vnum = dynamic_cast<VentureNumber *>(args.operands[i]);
    assert(vnum);
    prod *= vnum->getInt();
  }
  return new VentureNumber(prod);
}

VentureValue * IntDivideSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
    VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
    VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
    assert(d1);
    assert(d2);
    return new VentureNumber(d1->getInt() / d2->getInt());
}

VentureValue * IntEqualSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * d1 = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * d2 = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->getInt() == d2->getInt());
}

VentureValue * AtomEqualSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureAtom * d1 = dynamic_cast<VentureAtom *>(args.operands[0]);
  VentureAtom * d2 = dynamic_cast<VentureAtom *>(args.operands[1]);
  assert(d1);
  assert(d2);
  return new VentureBool(d1->n == d2->n);
}
