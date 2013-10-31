#ifndef TRACE_H
#define TRACE_H

#include <vector>
#include <unordered_map>
#include <string>

#include "value.h"
#include "node.h"
#include "scaffold.h"
#include "omegadb.h"
#include "env.h"
#include "exp.h"

#include <gsl/gsl_rng.h>
#include <boost/python/object.hpp>

class Trace
{
  /* Constructor will add nodes for primitives and environments. */

 public:
  Trace();
  
  /* These are the main methods wrapped by boost::python. */
  Expression parseExpression(boost::python::object o);
  void evalExpression(std::string addressName, boost::python::object object);
  double getDouble(std::string addressName);

  VentureValue * getValue(Address addr);
  bool containsAddr(Address addr) const { return _map.count(addr) == 1; }

  /* Global RNG for GSL */
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_taus);

  /* Outer mix-mh */
  Node * getRandomChoiceByIndex(uint32_t index) { return randomChoices[index]; }
  uint32_t numRandomChoices() { return randomChoices.size(); }

  double regen(const std::vector<Node *> & border,
	       Scaffold * scaffold,
	       bool shouldRestore,
	       OmegaDB & omegaDB);

  std::pair<double, OmegaDB> detach(const std::vector<Node *> & border,
				    Scaffold * scaffold);

  double evalFamily(Address address,
		    Expression & expression,
		    Environment environment,
		    Scaffold * scaffold,
		    bool shouldRestore,
		    OmegaDB & omegaDB);

  double unevalFamily(Node * node,
		      Scaffold * scaffold,
		      OmegaDB & omegaDB);



  
  Scaffold constructScaffold(std::vector<Node *> principalNodes,
			     unsigned int depth,
			     bool useDeltaKernels) const;


  Environment * getGlobalEnvironment() const;

private:

  std::unordered_map<Address,Node*> _map;

  Node * getNode(Address addr) const { return _map.at(addr); }


  /* Regen helpers */


  double regenParents(Node * node,
		      Scaffold * scaffold,
		      bool shouldRestore,
		      OmegaDB & omegaDB);

  double absorb(Node * node,
		Scaffold * scaffold,
		bool shouldRestore,
		OmegaDB & omegaDB);

  double constrain(Node * node, VentureValue * value);

  double regenInternal(Node * node,
		       Scaffold * scaffold,
		       bool shouldRestore,
		       OmegaDB & omegaDB);

  double applyPSP(Node * node,
		  Scaffold * scaffold,
		  bool shouldRestore,
		  OmegaDB & omegaDB);

  double evalRequests(Node * node,
		      Scaffold * scaffold,
		      bool shouldRestore,
		      OmegaDB & omegaDB);



  double eval(Address addr, 
	      Expression & exp, 
	      Address familyEnvAddr,
	      Scaffold * scaffold,
	      bool shouldRestore,
	      OmegaDB & omegaDB);

  double apply(Node * requestNode,
	       Node * outputNode,
	       Scaffold * scaffold,
	       bool shouldRestore,
	       OmegaDB & omegaDB);

  /* detach helpers */


  double detachParents(Node * node,
		       Scaffold * scaffold,
		       OmegaDB & omegaDB);


  double unabsorb(Node * node,
		  Scaffold * scaffold,
		  OmegaDB & omegaDB);

  double unconstrain(Node * node);

  double detachInternal(Node * node,
			Scaffold * scaffold,
			OmegaDB & omegaDB);

  double unapplyPSP(Node * node,
		    Scaffold * scaffold,
		    OmegaDB & omegaDB);

  double unevalRequests(Node * node,
			Scaffold * scaffold,
			OmegaDB & omegaDB);



  double uneval(Node * node,
		Scaffold * scaffold,
		OmegaDB & omegaDB);

  double unapply(Node * node,
		 Scaffold * scaffold,
		 OmegaDB & omegaDB);

  /* Misc */
  void addApplicationEdges(Node * requestNode, Node * outputNode, uint8_t numOperands);

  /* Create nodes: trace calls new */
  Node * makeNode(const Address & address, NodeType nodeType);

  /* Destroy node: trace calls delete */
  void destroyNode(Node * node);

  /* May return nullptr? (undecided) */
  Node * findSymbol(std::string symbol, Address environmentAddress);

  void registerRandomChoice(Node * node);
  void unregisterRandomChoice(Node * node);

  /* (Arbitrary ergodic, for latents)  */
  void registerAEKernel(Node * node);
  void unregisterAEKernel(Node * node);

  /* Part of initialization. */
  void addEnvironments();
  void addPrimitives();
  
  std::unordered_map<Node *, uint32_t> rcToIndex;
  std::vector<Node *> randomChoices;

};


#endif
