// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#include "sps/msp.h"
#include "sprecord.h"
#include "env.h"
#include "utils.h"

VentureValuePtr MakeMSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("mem", args, 1);
  return VentureValuePtr(new VentureSPRecord(new SP(new MSPRequestPSP(args->operandNodes[0]), new ESRRefOutputPSP())));
}

MSPRequestPSP::MSPRequestPSP(Node * sharedOperatorNode) : sharedOperatorNode(sharedOperatorNode) {}

VentureValuePtr quote(const VentureValuePtr& v)
{
  vector<VentureValuePtr> exp;
  exp.push_back(VentureValuePtr(new VentureSymbol("quote")));
  exp.push_back(v);
  return VentureValuePtr(new VentureArray(exp));
}

VentureValuePtr MSPRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> exp;
  exp.push_back(shared_ptr<VentureSymbol>(new VentureSymbol("memoizedSP")));
  
  for (size_t i = 0; i < args->operandValues.size(); ++i)
  {
    exp.push_back(quote(args->operandValues[i]));
  }
  
  shared_ptr<VentureEnvironment> empty(new VentureEnvironment());
  empty->addBinding("memoizedSP",sharedOperatorNode);
  
  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureArray(args->operandValues)),VentureValuePtr(new VentureArray(exp)),empty));
  
  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
