#ifndef TRACE_H
#define TRACE_H

#include "args.h"
#include "address.h"
#include <vector>
#include <map>
#include <unordered_map>
#include <string>
#include <gsl/gsl_rng.h>
#include <boost/python/object.hpp>

using namespace std;

struct VentureValue;
struct Node;
struct VentureEnvironment;
struct OmegaDB;
struct Scaffold;
struct SP;
struct SPAux;
struct VentureSP;
struct LatentDB;

struct Trace
{
  /* Constructor will add nodes for primitives and environments. */

  Trace();
  ~Trace();

  /* Global RNG for GSL */
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);

  /* Outer mix-mh */
  Node * getRandomChoiceByIndex(uint32_t index) { return randomChoices[index]; }
  uint32_t numRandomChoices() { return randomChoices.size(); }

  double regen(const vector<Node *> & border,
	       Scaffold * scaffold,
	       map<Node *,vector<double> > *gradients);

  double detach(const vector<Node *> & border,
		Scaffold * scaffold);


  pair<double, Node*> evalVentureFamily(size_t directiveID, VentureValue * expression,
					map<Node *,vector<double> > *gradients);


  /* Note: does not remove from ventureFamilies, so that destruction is easy.
     If I learn c++, there is probably a way to use a safe iterator. */
  double detachVentureFamily(Node * root);


  double unconstrain(Node * node,bool giveOwnershipToSP);
  
  Scaffold constructScaffold(vector<Node *> principalNodes,
			     unsigned int depth,
			     bool useDeltaKernels) const;

  vector<Node *> getRandomChoices(); // used by kernels

  map<size_t,pair<Node*,VentureValue*> > ventureFamilies;


//  unordered_map<size_t,Node*> definiteFamilies;

  /* Regen helpers */

  double regenParents(Node * node,
		      Scaffold * scaffold,
		      map<Node *,vector<double> > *gradients);

  double absorb(Node * node,
		Scaffold * scaffold,
		map<Node *,vector<double> > *gradients);


  // Eh, could pass gradients but don't need to
  double constrain(Node * node, VentureValue * value,bool reclaimValue);

  double regenInternal(Node * node,
		       Scaffold * scaffold,
		       map<Node *,vector<double> > *gradients);

  void processMadeSP(Node * node,bool isAAA);


  double applyPSP(Node * node,
		  Scaffold * scaffold,
		  map<Node *,vector<double> > *gradients);

  double evalRequests(Node * node,
		      Scaffold * scaffold,
		      map<Node *,vector<double> > *gradients);


  pair<double,Node*> evalFamily(Address addr,
				VentureValue * exp, 
				VentureEnvironment * familyEnv,
				Scaffold * scaffold,
				bool isDefinite,
				map<Node *,vector<double> > *gradients);


  // Meh, don't need to pass gradients
  double restoreSPFamily(VentureSP * vsp,
			 size_t id,
			 Node * root,
			 Scaffold * scaffold);

  double restoreFamily(Node * root,
		       Scaffold * scaffold);


  double restoreVentureFamily(Node * root);
  


  double apply(Node * requestNode,
	       Node * outputNode,
	       Scaffold * scaffold,
	       map<Node *,vector<double> > *gradients);

  /* detach helpers */


  double detachParents(Node * node,
		       Scaffold * scaffold);
	

  double unabsorb(Node * node,
		  Scaffold * scaffold);
	

  double detachInternal(Node * node,
			Scaffold * scaffold);


  void teardownMadeSP(Node * node,bool isAAA);

  double unapplyPSP(Node * node,
		    Scaffold * scaffold);


  double unevalRequests(Node * node,
			Scaffold * scaffold);


  double detachSPFamily(VentureSP * vsp,
			size_t id,
			Scaffold * scaffold);
	

  double detachFamily(Node * node,
		      Scaffold * scaffold);



  double unapply(Node * node,
		 Scaffold * scaffold);


  /* Misc */
  void addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes, Node * requestNode, Node * outputNode);

  void registerRandomChoice(Node * node);
  void unregisterRandomChoice(Node * node);

  void registerConstrainedChoice(Node *node);
  void unregisterConstrainedChoice(Node *node);

  /* (Arbitrary ergodic, for latents)  */
  void registerAEKernel(VentureSP * vsp);
  void unregisterAEKernel(VentureSP * vsp);

  /* Part of initialization. */
  void addPrimitives(const map<string,VentureValue *> & builtInValues,
		     const vector<SP *> & builtInSPs);

  void addEnvironments(const map<string,VentureValue *> & builtInValues,
		       const vector<SP *> & builtInSPs);

  Node * getSPAuxNode(SP * sp);

  VentureEnvironment * primitivesEnv;
  VentureEnvironment * globalEnv;
  
  unordered_map<Node *, uint32_t> rcToIndex;
  vector<Node *> randomChoices;

  unordered_map<Node *, uint32_t> ccToIndex;
  vector<Node *> constrainedChoices;

  // Bool is TRUE for detach
  map<pair<string,bool>,uint32_t> callCounts;


//////////////////////////////////////////////
  
  bool isReference(Node * node);
  void registerReference(Node * node, Node * lookedUpNode);
  Node * getSourceNode(Node * node);
  void setSourceNode(Node * node, Node * sourceNode);
  void clearSourceNode(Node * node);

  void setValue(Node * node, VentureValue * value);
  void clearValue(Node * node);
  VentureValue * getValue(Node * node);

  SP * getSP(Node * node);
  VentureSP * getVSP(Node * node);
  SPAux * getSPAux(Node * node);
  SPAux * getMadeSPAux(Node * makerNode);
  Args getArgs(Node * node);
  vector<Node *> getESRParents(Node * node);
  
  void constrainChoice(Node * node);
  void unconstrainChoice(Node * node);

  void setConstrained(Node * node,bool isConstrained);
  void setNodeOwnsValue(Node * node,bool giveOwnershipToSP);

  Node * removeLastESREdge(Node * outputNode);
  void addESREdge(Node * esrParent,Node * outputNode);

  void disconnectLookup(Node * node);

  void preUnabsorb(Node * node) {}
  void preAbsorb(Node * node) {}
  void preUnapplyPSP(Node * node) {}
  void preApplyPSP(Node * node) {}
  void preUnevalRequests(Node * requestNode) {}
  void preEvalRequests(Node * requestNode) {}
  void preUnconstrain(Node * node) {}
  void preConstrain(Node * node) {}

  void extractLatentDB(SP * sp,LatentDB * latentDB);
  void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType);
  void extractValue(Node * node, VentureValue * value);
  void prepareLatentDB(SP * sp);
  LatentDB * getLatentDB(SP * sp);
  void processDetachedLatentDB(SP * sp, LatentDB * latentDB);

  void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values);
  void registerSPFamily(Node * makerNode,size_t id,Node * root);



  

  // Since calling regen or detach with an omegaDB mutates the trace, we can only do so for one omegaDB at a time,
  // so we can make it a (temporary) variable for the trace.
  // Then we can call methods like extractValue() or extractLatents() that particles can override.
  void setOptions(bool shouldRestore, OmegaDB * omegaDB);
  bool shouldRestore{false};
  OmegaDB * omegaDB{nullptr};

};


#endif
