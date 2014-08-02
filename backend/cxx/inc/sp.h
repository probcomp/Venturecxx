#ifndef SP_H
#define SP_H

#include <iostream>
#include <memory>
#include <vector>
#include <gsl/gsl_rng.h>

using namespace std;

#include <boost/python/object.hpp>

struct SPAux;
struct LKernel;
struct VentureValue;
struct VentureToken;
struct Node;
struct LatentDB;
struct HSR;
struct VariationalLKernel;

enum class NodeType;
enum class FlushType;
enum class ParameterScope;

/* Although this is not technically an abstract class, 
   one cannot have both simulate defaults at the same time,
   so it should be considered an abstract class. */
struct SP
{
  SP() {}
  SP(string name): name(name) {}

/* Simulate */
  VentureValue * simulate(Node * node, gsl_rng * rng) const;
  virtual VentureValue * simulateRequest(Node * node, gsl_rng * rng) const { return nullptr; }
  virtual VentureValue * simulateOutput(Node * node, gsl_rng * rng) const { return nullptr; }
  virtual double simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const { return 0; }

/* LogDensity */
  double logDensity(VentureValue * value, Node * node) const;
  virtual double logDensityRequest(VentureValue * value, Node * node) const { return 0; }
  virtual double logDensityOutput(VentureValue * value, Node * node) const { return 0; }
  virtual double logDensityOutputNumeric(double output, const vector<double> & args) const { return 0; }

/* Incorporate */
  void incorporate(VentureValue * value, Node * node) const;
  virtual void incorporateRequest(VentureValue * value, Node * node) const { }
  virtual void incorporateOutput(VentureValue * value, Node * node) const { }

/* Remove */
  void remove(VentureValue * value, Node * node) const;
  virtual void removeRequest(VentureValue * value, Node * node) const {}
  virtual void removeOutput(VentureValue * value, Node * node) const {}

/* Flush: may be called on both requests and outputs. */
  void flushValue(VentureValue * value, NodeType nodeType) const;
  virtual void flushRequest(VentureValue * value) const;
  virtual void flushOutput(VentureValue * value) const;
  virtual void flushFamily(SPAux * spaux, size_t id) const;

/* Can Absorb */
  bool canAbsorb(NodeType nodeType) const;

/* Is Random w MH proposal */
  bool isRandom(NodeType nodeType) const;

  /* SPAux */
  virtual SPAux * constructSPAux() const;

  virtual void destroySPAux(SPAux * spaux) const;


/* LatentDBs */
  virtual LatentDB * constructLatentDB() const { return nullptr; }
  virtual void destroyLatentDB(LatentDB * latentDB) const { }

/* LSRs */
  virtual double simulateLatents(SPAux * spaux,
				 HSR * hsr,
				 bool shouldRestore,
				 LatentDB * latentDB,
				 gsl_rng * rng) const { return 0; }

  virtual double detachLatents(SPAux * spaux,
			       HSR * hsr,
			       LatentDB * latentDB) const { return 0; }

  virtual void restoreAllLatents(SPAux * spaux, LatentDB * latentDB) {};

  virtual pair<double, LatentDB *> detachAllLatents(SPAux * spaux) const { return {0,nullptr}; }


  virtual double logDensityOfCounts(SPAux * spaux) const { assert(false); return 0; }

  /* Right now this calls NEW, which I don't like. Either it is an attribute of
     the SP class, or its methods are dumped into the bloat. */
  virtual LKernel * getAAAKernel() const;

  virtual VariationalLKernel * getVariationalLKernel(Node * node) const;
  virtual vector<ParameterScope> getParameterScopes() const { assert(false); return vector<ParameterScope> {}; }

  virtual vector<double> gradientOfLogDensity(double output,
				      const vector<double> & arguments) const 
    { assert(false); return vector<double> {}; }



  bool hasAux() { return makesESRs || makesHSRs || tracksSamples; }
  bool isNullRequest() { return !makesESRs && !makesHSRs; }

  bool tracksSamples{false};

  bool canAbsorbRequest{true};
  bool canAbsorbOutput{false};

  bool isRandomRequest{false};
  bool isRandomOutput{false};

  bool isESRReference{false};

  bool makesESRs{false};
  bool makesHSRs{false};

  bool childrenCanAAA{false};

  bool hasVariationalLKernel{false};

  bool hasAEKernel{false};

  bool canEnumerate(NodeType nodeType) const;
  bool canEnumerateRequest{false};
  bool canEnumerateOutput{false};

  string name{"sp_no_name"};

  vector<VentureValue*> enumerate(Node * node) const;
  /* TODO for expediency, these only return the OTHER values, but we would want
     them to return all values and then we loop through and compare for equality
     later in the pipeline. */
  virtual vector<VentureValue*> enumerateOutput(Node * node) const;
  virtual vector<VentureValue*> enumerateRequest(Node * node) const;

  Node * findFamily(size_t id, SPAux * spaux);

  void registerFamily(size_t id, Node * root, SPAux * spaux);



  /* Does not flush. */
  Node * detachFamily(size_t id, SPAux * spaux);

  
  boost::python::object toPython(VentureToken * token) 
    { return boost::python::object("<sp object>"); }


  bool isValid() { return magic == 5390912; }
  uint32_t magic = 5390912;
  virtual ~SP() { assert(isValid()); magic = 0; }; 


};



#endif
