// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "lkernel.h"
#include "psp.h"
#include "sp.h"
#include "sprecord.h"

VentureValuePtr DeterministicMakerAAALKernel::simulate(
    Trace * trace, const boost::shared_ptr<Args> & args, gsl_rng * rng)
{
  boost::shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(makerPSP->simulate(args, rng));

  spRecord->spAux = args->aaaMadeSPAux;
  return spRecord;
}

double DeterministicMakerAAALKernel::weight(
    Trace * trace,
    const VentureValuePtr & value,
    const boost::shared_ptr<Args> & args)
{
  boost::shared_ptr<VentureSPRecord> spRecord = dynamic_pointer_cast<VentureSPRecord>(value);
  assert(spRecord);
  return spRecord->sp->outputPSP->logDensityOfData(spRecord->spAux);
}

VentureValuePtr DeterministicLKernel::simulate(
    Trace * trace,
    const boost::shared_ptr<Args> & args,
    gsl_rng * rng)
{
  return value;
}

double DeterministicLKernel::weight(
    Trace * trace,
    const VentureValuePtr & value,
    const boost::shared_ptr<Args> & args)
{
  return psp->logDensity(value, args);
}
