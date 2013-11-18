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
struct VentureEnvironment;
struct Particle;
struct Scaffold;
struct SP;
struct VentureSP;


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

  double generate(const vector<Node *> & border,
	       Scaffold * scaffold,
		  Particle * xi);

  void commit(Particle * omega);

  double extract(const vector<Node *> & border,
				 Scaffold * scaffold,
				 Particle * rho);

  pair<double, Node*> evalVentureFamily(size_t directiveID, 
					VentureValue * expression);


  double constrain(Node * node,VentureValue * value, Particle * xi);

  double unconstrain(Node * node,bool giveOwnershipToSP,Particle * rho);
  
  Scaffold constructScaffold(vector<Node *> principalNodes,
			     unsigned int depth,
			     bool useDeltaKernels) const;

  vector<Node *> getRandomChoices(); // used by kernels

  map<size_t,pair<Node*,VentureValue*> > ventureFamilies;


  /* Generate helpers */

  double generateParents(Node * node,
		      Scaffold * scaffold,
			 Particle * xi);

  double absorb(Node * node,
		Scaffold * scaffold,
		Particle * xi);


  double constrain(Node * node, VentureValue * value,bool reclaimValue,Particle * xi);

  double generateInternal(Node * node,
		       Scaffold * scaffold,
			  Particle * xi);

  void processMadeSP(Node * node,bool isAAA,Particle * xi);

  void processMadeSP(Node * node);


  double applyPSP(Node * node,
		  Scaffold * scaffold,
		  Particle * xi);

  double evalRequests(Node * node,
		      Scaffold * scaffold,
		      Particle * xi);

  pair<double,Node*> evalFamily(VentureValue * exp, 
				VentureEnvironment * familyEnv,
				Scaffold * scaffold,
				Particle * xi);

  double apply(Node * requestNode,
	       Node * outputNode,
	       Scaffold * scaffold,
	       Particle * xi);

  /* extract helpers */


  double extractParents(Node * node,
			Scaffold * scaffold,
			Particle * rho);


  double unabsorb(Node * node,
		  Scaffold * scaffold,
		  Particle * rho);


  double extractInternal(Node * node,
			 Scaffold * scaffold,
			 Particle * rho);

  void teardownMadeSP(Node * node,bool isAAA,Particle * rho);

  double unapplyPSP(Node * node,
		    Scaffold * scaffold,
		    Particle * rho);

  double unevalRequests(Node * node,
			Scaffold * scaffold,
			Particle * rho);

  double extractSPFamily(VentureSP * vsp,
			size_t id,
			Scaffold * scaffold,
			Particle * rho);

  double extractFamily(Node * node,
		       Scaffold * scaffold,
		       Particle * rho);

  double unapply(Node * node,
		 Scaffold * scaffold,
		 Particle * rho);

  /* Misc */
  void addApplicationEdges(Node * operatorNode,const vector<Node *> & operandNodes, Node * requestNode, Node * outputNode);

  void registerRandomChoice(Node * node);
  void unregisterRandomChoice(Node * node);

  void registerConstrainedChoice(Node *node);
  void unregisterConstrainedChoice(Node *node);


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

  // Bool is TRUE for extract
  map<pair<string,bool>,uint32_t> callCounts;
};


#endif
