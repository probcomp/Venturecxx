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
  virtual ~Trace();

  /* Global RNG for GSL */
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);

  /* Outer mix-mh */
  Node * getRandomChoiceByIndex(uint32_t index) { return randomChoices[index]; }
  virtual uint32_t numRandomChoices() { return randomChoices.size(); }

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

  virtual void decrementRegenCount(Node * node, Scaffold * scaffold);
  virtual void incrementRegenCount(Node * node, Scaffold * scaffold);
  virtual int getRegenCount(Node * node, Scaffold * scaffold);

  virtual bool isReference(Node * node);
  virtual void registerReference(Node * node, Node * lookedUpNode);
  virtual Node * getSourceNode(Node * node);
  virtual void setSourceNode(Node * node, Node * sourceNode);
  virtual void clearSourceNode(Node * node);

  virtual void setValue(Node * node, VentureValue * value);
  virtual void clearValue(Node * node);
  virtual VentureValue * getValue(Node * node);

  virtual SP * getSP(Node * node);
  virtual VentureSP * getVSP(Node * node);
  virtual SPAux * getSPAux(Node * node);
  virtual SPAux * getMadeSPAux(Node * makerNode);
  virtual Args getArgs(Node * node);
  virtual vector<Node *> getESRParents(Node * node);
  
  virtual void constrainChoice(Node * node);
  virtual void unconstrainChoice(Node * node);

  virtual void registerRandomChoice(Node * node);
  virtual void unregisterRandomChoice(Node * node);

  virtual void clearConstrained(Node * node);
  virtual void setConstrained(Node * node);

  virtual void setNodeOwnsValue(Node * node);
  virtual void clearNodeOwnsValue(Node * node);

  virtual void disconnectLookup(Node * node);
  virtual void reconnectLookup(Node * node);
  virtual void connectLookup(Node * node, Node * lookedUpNode);

  virtual Node * removeLastESREdge(Node * outputNode);
  virtual void addESREdge(Node * esrParent,Node * outputNode);

  virtual void detachMadeSPAux(Node * makerNode);
  virtual void regenMadeSPAux(Node * makerNode, SP * sp);

  virtual void preUnabsorb(Node * node) {}
  virtual void preAbsorb(Node * node) {}
  virtual void preUnapplyPSP(Node * node) {}
  virtual void preApplyPSP(Node * node) {}
  virtual void preUnevalRequests(Node * requestNode) {}
  virtual void preEvalRequests(Node * requestNode) {}
  virtual void preUnconstrain(Node * node) {}
  virtual void preConstrain(Node * node) {}

  virtual void extractLatentDB(SP * sp,LatentDB * latentDB);
  virtual void registerGarbage(SP * sp,VentureValue * value,NodeType nodeType);
  virtual void extractValue(Node * node, VentureValue * value);
  virtual void prepareLatentDB(SP * sp);
  virtual LatentDB * getLatentDB(SP * sp);
  virtual void processDetachedLatentDB(SP * sp, LatentDB * latentDB);

  virtual void registerSPOwnedValues(Node * makerNode, size_t id, const vector<VentureValue*> & values);
  virtual void registerSPFamily(Node * makerNode,size_t id,Node * root);

  virtual void clearVSPMakerNode(VentureSP * vsp, Node * makerNode);
  virtual void setVSPMakerNode(VentureSP * vsp, Node * makerNode);

  // Since calling regen or detach with an omegaDB mutates the trace, we can only do so for one omegaDB at a time,
  // so we can make it a (temporary) variable for the trace.
  // Then we can call methods like extractValue() or extractLatents() that particles can override.
  void setOptions(bool shouldRestore, OmegaDB * omegaDB);
  bool shouldRestore{false};
  OmegaDB * omegaDB{nullptr};

};


#endif
