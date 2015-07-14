// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

#include "sp.h"
#include "node.h"
#include "psp.h"
#include "concrete_trace.h"
#include "stop-and-copy.h"

bool SPFamilies::containsFamily(FamilyID id)  { return families.count(id); }
RootOfFamily SPFamilies::getRootOfFamily(FamilyID id) 
{
  assert(families.count(id));
  return families[id];
}

void SPFamilies::registerFamily(FamilyID id,RootOfFamily root)
{
  assert(!families.count(id));
  families[id] = root;
}

void SPFamilies::unregisterFamily(FamilyID id)
{
  assert(families.count(id));
  families.erase(id);
}

boost::shared_ptr<SPAux> SPAux::clone()
{
  ForwardingMap m = ForwardingMap();
  return boost::shared_ptr<SPAux>(this->copy_help(&m));
}

boost::shared_ptr<LatentDB> SP::constructLatentDB() const { return boost::shared_ptr<LatentDB>(); }

SP::SP(PSP * requestPSP, PSP * outputPSP) :
  requestPSP(boost::shared_ptr<PSP>(requestPSP)),
  outputPSP(boost::shared_ptr<PSP>(outputPSP))
  {}

double SP::simulateLatents(boost::shared_ptr<SPAux> spaux,boost::shared_ptr<LSR> lsr,bool shouldRestore,boost::shared_ptr<LatentDB> latentDB,gsl_rng * rng) const { assert(false); throw "no default latent handling"; }
double SP::detachLatents(boost::shared_ptr<SPAux> spaux,boost::shared_ptr<LSR> lsr,boost::shared_ptr<LatentDB> latentDB) const { assert(false); throw "no default latent handling"; }


boost::shared_ptr<PSP> SP::getPSP(ApplicationNode * node) const
{
  if (dynamic_cast<RequestNode*>(node)) { return requestPSP; }
  else { return outputPSP; }
}

void SP::AEInfer(boost::shared_ptr<SPAux> spAux, boost::shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }

boost::python::object SPAux::toPython(Trace * trace) const
{
  // this is only called on subclasses of SPAux to display the
  // associated procedures. TODO: teach those procedures to use
  // SPAux::asVentureValue instead.
  throw "unknown spAux";
}

VentureValuePtr SPAux::asVentureValue() const
{
  return VentureValuePtr(new VentureNil());
}


boost::python::dict SP::toPython(Trace * trace, boost::shared_ptr<SPAux> spAux) const
{
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = "<procedure>";
  if (spAux) {
    value["aux"] = spAux->asVentureValue()->toPython(trace);
  } else {
    VentureValuePtr nil(new VentureNil());
    value["aux"] = nil->toPython(trace);
  }
  return value;
}

boost::python::dict VentureSPRef::toPython(Trace * trace) const 
{
  return trace->getMadeSP(makerNode)->toPython(trace, trace->getMadeSPAux(makerNode));
}

bool VentureSPRef::equals(const VentureValuePtr & other) const
{
  boost::shared_ptr<VentureSPRef> other_v = dynamic_pointer_cast<VentureSPRef>(other);
  return other_v && (other_v->makerNode == makerNode);
}

size_t VentureSPRef::hash() const 
{ 
  boost::hash<long> long_hash;
  return long_hash(reinterpret_cast<long>(makerNode));
}

string VentureSPRef::toString() const { return "spRef"; }
