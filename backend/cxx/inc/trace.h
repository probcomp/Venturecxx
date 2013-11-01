#ifndef TRACE_H
#define TRACE_H

#include <vector>
#include <map>
#include <unordered_map>
#include <string>

#include <gsl/gsl_rng.h>
#include <boost/python/object.hpp>

using namespace std;

struct VentureValue;
struct Node;
struct Expression;
struct Environment;
struct OmegaDB;
struct Scaffold;
struct SP;
struct VentureSP;

class Trace
{
  /* Constructor will add nodes for primitives and environments. */

 public:
  Trace();
  ~Trace();

  /* Global RNG for GSL */
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);

  /* Outer mix-mh */
  Node * getRandomChoiceByIndex(uint32_t index) { return randomChoices[index]; }
  uint32_t numRandomChoices() { return randomChoices.size(); }

  double regen(const vector<Node *> & border,
	       Scaffold & scaffold,
	       bool shouldRestore,
	       OmegaDB & omegaDB);

  pair<double, OmegaDB> detach(const vector<Node *> & border,
				    Scaffold & scaffold);


  pair<double, Node*> evalVentureFamily(size_t directiveID, Expression & expression);

  /* Note: does not remove from ventureFamilies, so that destruction is easy.
     If I learn c++, there is probably a way to use a safe iterator. */
  double detachVentureFamily(Node * root, OmegaDB & omegaDB);

  double constrain(Node * node,bool reclaimValue);

  double unconstrain(Node * node);
  
  Scaffold constructScaffold(vector<Node *> principalNodes,
			     unsigned int depth,
			     bool useDeltaKernels) const;

  Environment * getGlobalEnvironment() const;

protected:

  unordered_map<size_t,Node*> definiteFamilies;

  /* Regen helpers */

  double regenParents(Node * node,
		      Scaffold & scaffold,
		      bool shouldRestore,
		      OmegaDB & omegaDB);

  double absorb(Node * node,
		Scaffold & scaffold,
		bool shouldRestore,
		OmegaDB & omegaDB);


  double constrain(Node * node, VentureValue * value,bool reclaimValue);

  double regenInternal(Node * node,
		       Scaffold & scaffold,
		       bool shouldRestore,
		       OmegaDB & omegaDB);

  void processMadeSP(Node * node);


  double applyPSP(Node * node,
		  Scaffold & scaffold,
		  bool shouldRestore,
		  OmegaDB & omegaDB);

  double evalRequests(Node * node,
		      Scaffold & scaffold,
		      bool shouldRestore,
		      OmegaDB & omegaDB);

  pair<double,Node*> evalSPFamily(Expression & exp,
					       Environment & env,
					       Scaffold & scaffold,
					       OmegaDB & omegaDB);


  pair<double,Node*> evalFamily(Expression & exp, 
				     Node * familyEnvNode,
				     Scaffold & scaffold,
				     OmegaDB & omegaDB,
				     bool isDefinite);


  double restoreSPFamily(Node * root,
			Scaffold & scaffold,
			OmegaDB & omegaDB);

  double restoreFamily(Node * root,
			Scaffold & scaffold,
			OmegaDB & omegaDB);

  double restoreVentureFamily(Node * root);
  





  double apply(Node * requestNode,
	       Node * outputNode,
	       Scaffold & scaffold,
	       bool shouldRestore,
	       OmegaDB & omegaDB);

  /* detach helpers */


  double detachParents(Node * node,
		       Scaffold & scaffold,
		       OmegaDB & omegaDB);


  double unabsorb(Node * node,
		  Scaffold & scaffold,
		  OmegaDB & omegaDB);


  double detachInternal(Node * node,
			Scaffold & scaffold,
			OmegaDB & omegaDB);

  void teardownMadeSP(Node * node);

  double unapplyPSP(Node * node,
		    Scaffold & scaffold,
		    OmegaDB & omegaDB);

  double unevalRequests(Node * node,
			Scaffold & scaffold,
			OmegaDB & omegaDB);

  double detachSPFamily(VentureSP * vsp,
			size_t id,
			Scaffold & scaffold,
			OmegaDB & omegaDB);

  double detachFamily(Node * node,
		      Scaffold & scaffold,
		      OmegaDB & omegaDB);

  double unapply(Node * node,
		 Scaffold & scaffold,
		 OmegaDB & omegaDB);

  /* Misc */
  void addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes, Node * requestNode, Node * outputNode);

  void registerRandomChoice(Node * node);
  void unregisterRandomChoice(Node * node);

  /* (Arbitrary ergodic, for latents)  */
  void registerAEKernel(VentureSP * vsp);
  void unregisterAEKernel(VentureSP * vsp);

  /* Part of initialization. */
  void addPrimitives(const map<string,VentureValue *> & builtInValues,
		     const vector<SP *> & builtInSPs);

  void addEnvironments(const map<string,VentureValue *> & builtInValues,
		       const vector<SP *> & builtInSPs);

  Node * getSPAuxNode(SP * sp);

  Node * globalEnvNode;
  
  unordered_map<Node *, uint32_t> rcToIndex;
  vector<Node *> randomChoices;

  map<size_t,Node*> ventureFamilies;
};


#endif
