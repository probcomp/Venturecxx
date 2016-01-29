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

#include "sps/csp.h"
#include "sprecord.h"
#include "env.h"
#include "utils.h"

#include <boost/foreach.hpp>

VentureValuePtr MakeCSPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("lambda", args, 2);

  vector<string> symbols;
  BOOST_FOREACH(VentureValuePtr v, args->operandValues[0]->getArray())
  {
    symbols.push_back(v->getSymbol());
  }

  VentureValuePtr expression = args->operandValues[1];
  CSPRequestPSP* req = new CSPRequestPSP(symbols, expression, args->env);
  return VentureValuePtr(new VentureSPRecord(new SP(req, new ESRRefOutputPSP())));
}

CSPRequestPSP::CSPRequestPSP(const vector<string>& symbols,
                             VentureValuePtr expression,
                             shared_ptr<VentureEnvironment> environment) :
  symbols(symbols),
  expression(expression),
  environment(environment)
{}

VentureValuePtr CSPRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("compound procedure", args, symbols.size());

  shared_ptr<VentureEnvironment> extendedEnv =
    shared_ptr<VentureEnvironment>(new VentureEnvironment(environment));

  for (size_t i = 0; i < symbols.size(); ++i)
  {
    extendedEnv->addBinding(symbols[i], args->operandNodes[i]);
  }

  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),expression,extendedEnv));

  return VentureValuePtr(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}
