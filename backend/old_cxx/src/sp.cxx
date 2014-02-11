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
#include "sp.h"
#include "flush.h"
#include "node.h"
#include "lkernel.h"
#include "infer/meanfield.h"
#include "spaux.h"
#include "value.h"
#include "utils.h"

#include <iostream>

/* All of these methods simply check the node type, and dispatch
   to REQUEST or OUTPUT as appropriate. */

VentureValue * SP::simulate(Node * node, gsl_rng * rng) const
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->simulateRequest(node,rng); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->simulateOutput(node,rng); 
  }
}

double SP::logDensity(VentureValue * value, Node * node) const
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->logDensityRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->logDensityOutput(value,node); 
  }
}

void SP::incorporate(VentureValue * value, Node * node) const
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->incorporateRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->incorporateOutput(value,node); 
  }
}


void SP::remove(VentureValue * value, Node * node) const
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->removeRequest(value,node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->removeOutput(value,node); 
  }
}

vector<VentureValue*> SP::enumerate(Node * node) const
{
  if (node->nodeType == NodeType::REQUEST)
  { return this->enumerateRequest(node); }
  else 
  { 
    assert(node->nodeType == NodeType::OUTPUT);
    return this->enumerateOutput(node); 
  }
}


bool SP::canAbsorb(NodeType nodeType) const
{
  if (nodeType == NodeType::REQUEST)
  { return canAbsorbRequest; }
  else 
  { 
    assert(nodeType == NodeType::OUTPUT);
    return canAbsorbOutput; 
  }
}

bool SP::isRandom(NodeType nodeType) const
{
  if (nodeType == NodeType::REQUEST)
  { return isRandomRequest; }
  else 
  { 
    assert(nodeType == NodeType::OUTPUT);
    return isRandomOutput; 
  }
}

bool SP::canEnumerate(NodeType nodeType) const
{
  if (nodeType == NodeType::REQUEST)
  { return canEnumerateRequest; }
  else 
  { 
    assert(nodeType == NodeType::OUTPUT);
    return canEnumerateOutput; 
  }
}

void SP::flushValue(VentureValue * value, NodeType nodeType) const
{
  assert(this);
  assert(value);
  switch (nodeType)
  {
  case NodeType::REQUEST: { flushRequest(value); return; }
  case NodeType::OUTPUT: { flushOutput(value); return; }
  default: { assert(false); }
  }
}

LKernel * SP::getAAAKernel() const { return new DefaultAAAKernel(this); }

Node * SP::findFamily(size_t id, SPAux * spaux) 
{
  assert(spaux);
  if (spaux->families.count(id)) { return spaux->families[id]; }
  else { return nullptr; }
}

void SP::registerFamily(size_t id, Node * root, SPAux * spaux) 
{
  assert(spaux);
  assert(!spaux->families.count(id));
  spaux->families[id] = root;
}

/* Does not flush. */
Node * SP::detachFamily(size_t id, SPAux * spaux) 
{ 
  assert(spaux);
  assert(dynamic_cast<SPAux *>(spaux));
  assert(spaux->families.count(id));
  Node * root = spaux->families[id];
  assert(root);
  spaux->families.erase(id);
  return root;
}

SPAux * SP::constructSPAux() const 
    { 
      SPAux * spaux = new SPAux;
      return spaux;
    }
void SP::destroySPAux(SPAux * spaux) const 
    { 
      delete spaux; 
    }

void SP::flushRequest(VentureValue * value) const { delete value; }
void SP::flushOutput(VentureValue * value) const { delete value; };
void SP::flushFamily(SPAux * spaux, size_t id) const { } 

vector<VentureValue*> SP::enumerateRequest(Node * node) const
{
  vector<VentureValue*> v;
  return v;
}

vector<VentureValue*> SP::enumerateOutput(Node * node) const
{
  vector<VentureValue*> v;
  return v;
}

VariationalLKernel * SP::getVariationalLKernel(Node * node) const
{
  return new DefaultVariationalLKernel(this,node);
}
