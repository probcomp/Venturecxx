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
  for (size_t i = border.size()-1; i >= 0; --i)
  {
    Node * node = border[i];
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





double unconstrain(Trace * trace,Node * node)
{ assert(false); }
double detach(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double extractParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double extractESRParents(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double extract(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double unevalFamily(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double unapply(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
void teardownMadeSP(Trace * trace,Node * node,bool isAAA)
{ assert(false); }
double unapplyPSP(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }
double unevalRequests(Trace * trace,Node * node,shared_ptr<Scaffold> scaffold,DB * db)
{ assert(false); }

