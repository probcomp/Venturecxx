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

VentureValue * SP::simulate(const Args & args, gsl_rng * rng) const
{
  if (args.isRequest)
  { return this->simulateRequest(args,rng); }
  else 
  { 
    return this->simulateOutput(args,rng); 
  }
}

double SP::logDensity(VentureValue * value, const Args & args) const
{
  if (args.isRequest)
  { return this->logDensityRequest(value,args); }
  else 
  { 
    return this->logDensityOutput(value,args); 
  }
}

void SP::incorporate(VentureValue * value, const Args & args) const
{
  if (args.isRequest)
  { return this->incorporateRequest(value,args); }
  else 
  { 
    return this->incorporateOutput(value,args); 
  }
}


void SP::remove(VentureValue * value, const Args & args) const
{
  if (args.isRequest)
  { return this->removeRequest(value,args); }
  else 
  { 
    return this->removeOutput(value,args); 
  }
}

vector<VentureValue*> SP::enumerate(const Args & args) const
{
  if (args.isRequest)
  { return this->enumerateRequest(args); }
  else 
  { 
    return this->enumerateOutput(args); 
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

vector<VentureValue*> SP::enumerateRequest(const Args & args) const
{
  vector<VentureValue*> v;
  return v;
}

vector<VentureValue*> SP::enumerateOutput(const Args & args) const
{
  vector<VentureValue*> v;
  return v;
}

VariationalLKernel * SP::getVariationalLKernel(const Args & args) const
{
  return new DefaultVariationalLKernel(this,args);
}
