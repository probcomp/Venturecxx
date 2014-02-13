#include "detach.h"
#include "node.h"
#include "trace.h"
#include "scaffold.h"
#include "db.h"
#include "sp.h"
#include "psp.h"

pair<double,shared_ptr<DB> > detachAndExtract(Trace * trace,const vector<Node*> & border,shared_ptr<Scaffold> scaffold)
{
  double weight = 0;
  shared_ptr<DB> db(new DB());
  for (vector<Node*>::const_reverse_iterator borderIter = border.rbegin();
       borderIter != border.rend();
       ++borderIter)
  {
    Node * node = *borderIter;
    if (scaffold->isAbsorbing(node)) 
    {
      ApplicationNode * appNode = dynamic_cast<ApplicationNode*>(node);
      assert(appNode);
      weight += detach(trace,appNode,scaffold,db);
    }
    else
    {
      if (trace->isObservation(node))
      {
	weight += unconstrain(trace,trace->getOutermostNonRefAppNode(node)); 
      }
      weight += extract(trace,node,scaffold,db);
    }
  }
  return make_pair(weight,db);
}


double unconstrain(Trace * trace,OutputNode * node)
{
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr value = trace->getValue(node);

  trace->unregisterConstrainedChoice(node);
  psp->unincorporate(value,args);
  double weight = psp->logDensity(value,args);
  psp->incorporate(value,args);
  return weight;
}

double detach(Trace * trace,ApplicationNode * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  shared_ptr<PSP> psp = trace->getMadeSP(trace->getOperatorSPMakerNode(node))->getPSP(node);
  shared_ptr<Args> args = trace->getArgs(node);
  VentureValuePtr groundValue = trace->getGroundValue(node);

  psp->unincorporate(groundValue,args);
  double weight = psp->logDensity(groundValue,args);
  weight += extractParents(trace,node,scaffold,db);
  return weight;
}


double extractParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = extractESRParents(trace,node,scaffold,db);
  for (vector<Node*>::reverse_iterator defParentIter = node->definiteParents.rbegin();
       defParentIter != node->definiteParents.rend();
       ++defParentIter)
  {
    weight += extract(trace,*defParentIter,scaffold,db);
  }
  return weight;
}

double extractESRParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{
  double weight = 0;
  vector<Node*> esrParents = trace->getESRParents(node);
  for (vector<Node*>::reverse_iterator esrParentIter = esrParents.rbegin();
       esrParentIter != esrParents.rend();
       ++esrParentIter)
  {
    weight += extract(trace,*esrParentIter,scaffold,db);
  }
  return weight;
}



double extract(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{ assert(false); }
double unevalFamily(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{ assert(false); }
double unapply(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{ assert(false); }
void teardownMadeSP(Trace * trace,Node * node,bool isAAA)
{ assert(false); }
double unapplyPSP(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{ assert(false); }
double unevalRequests(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,shared_ptr<DB> db)
{ assert(false); }

