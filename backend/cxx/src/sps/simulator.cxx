/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "value.h"
#include "utils.h"
#include "node.h"
#include "sp.h"
#include "string.h"
#include "sps/simulator.h"

VentureValue * MakeSimulatorSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureSymbol * vsubfolder = dynamic_cast<VentureSymbol *>(operands[0]->getValue());
  assert(vsubfolder);
  return new VentureSP(new SimulatorSP(vsubfolder->sym));
}

// PARAMS must be a VentureVector consisting of VentureNumbers
string constructParamStringFromVector(VentureVector * params)
{
  Vector<VentureValue*> xs = params->xs;
  string s = "[";
  for (VentureValue * v : xs)
  {
    VentureNumber * vnum = dynamic_cast<VentureNumber *>(v);
    s += std::to_string(vnum->x);
    s += ",";
  }
  s += "]";
  return s;
}

VentureValue * SimulatorSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  SimulatorSPAux * spaux = dynamic_cast<SimulatorSPAux *>(node->spaux());
  assert(spaux);

  vector<Node *> & operands = node->operandNodes;
  VentureSymbol * vmethodname = dynamic_cast<VentureSymbol *>(operands[0]->getValue());
  assert(vmethodname);
  if (vmethodname->sym == "simulate")
  {
    // args = ("simulate",old_state::VentureSimulatorToken,params::VentureVector{VentureNumber}
    VentureSimulatorToken * voldState = dynamic_cast<VentureSimulatorToken *>(operands[1]->getValue());
    assert(voldState);

    VentureVector * vparams =  dynamic_cast<VentureVector *>(operands[2]->getValue());
    assert(vparams);

    uint32_t nextFileID = spaux->next_id++;
    string paramString = constructParamStringFromVector(params);

    string expression = "simulate(" + voldState->fileID + "," + nextFileID + "," + paramString + ")";

    engEvalString(spaux->ep, expression);
    return new VentureSimulatorToken(nextFileID);
  } 
  else if(vmethodname->sym == "initialize")
  {
    // args = ("initialize")
    uint32_t nextFileID = spaux->next_id++;
    string expression = "initialize(" + nextFileID + ")";
    engEvalString(spaux->ep, expression); // TODO UNCOMMENT
    return new VentureSimulatorToken(nextFileID);
  }

  else if(vmethodname->sym == "emit")
  {
    // args = ("emit",old_state::VentureSimulatorToken)
    VentureSimulatorToken * vstate = dynamic_cast<VentureSimulatorToken *>(operands[1]->getValue());
    assert(vstate);
    uint32_t nextFileID = spaux->next_id++;
    string expression = "emit(" + vstate->fileID + "," + nextFileID + ")";
    return new VentureSimulatorToken(nextFileID);
  }
  else if (vmethodname->sym == "distance")
  {
    VentureSimulatorToken * vrealEmission = dynamic_cast<VentureSimulatorToken *>(operands[1]->getValue());
    assert(vrealEmission);

    VentureSimulatorToken * vobservedEmission = dynamic_cast<VentureSimulatorToken *>(operands[2]->getValue());
    assert(vobservedEmission);

    string expression = "computed_distance = distance(" + vrealEmission->fileID + "," + vobservedEmission->fileID + ")";
    engEvalString(spaux->ep, expression);
    double computedDistance = engGetVariable(spaux->ep, "computed_distance");
    engEvalString(spaux->ep, "clear(x)");
    return new VentureNumber(nextFileID);

  }
  else { assert(false); }
}

SPAux * SimulatorSP::constructSPAux() const
{
  SimulatorSPAux * spaux = new SimulatorSPAux();
  spaux->ep = engOpen("");
  engEvalString(spaux->ep, "cd pathToFolder"); // TODO UNCOMMENT
  return spaux;
}

void SimulatorSP::destroySPAux(SPAux *spaux) const
{
  engClose(spaux->ep);
  delete spaux;
}
