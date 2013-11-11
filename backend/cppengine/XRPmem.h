
#ifndef VENTURE___XRPMEM_H
#define VENTURE___XRPMEM_H

#include "Analyzer.h"
#include "Evaluator.h"
#include "MHProposal.h"
#include "XRPCore.h"

struct NodeApplicationCaller;

struct XRP__memoizer_map_element {
  XRP__memoizer_map_element()
  {
    throw std::runtime_error("Default constructor should not be evaluated.");
  }
  XRP__memoizer_map_element(shared_ptr<NodeApplicationCaller> application_caller_node)
    : application_caller_node(application_caller_node),
      hidden_uses(0),
      active_uses(0)
  {}

  shared_ptr<NodeApplicationCaller> application_caller_node;
  size_t hidden_uses;
  size_t active_uses;
};

class XRP__memoizer : public XRP { // So called "mem-maker".
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >&,
                                       shared_ptr<VentureValue>);
  virtual void Incorporate(vector< shared_ptr<VentureValue> >&,
                                shared_ptr<VentureValue>);
  virtual void Remove(vector< shared_ptr<VentureValue> >&,
                           shared_ptr<VentureValue>);

public:
  virtual bool IsRandomChoice();
  virtual bool CouldBeRescored();
  virtual string GetName();
};

string XRP__memoized_procedure__MakeMapKeyFromArguments(vector< shared_ptr<VentureValue> >& arguments);

class XRP__memoized_procedure : public XRP { // So called "mem-sampler".
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >&,
                                       shared_ptr<VentureValue>);
  virtual void Incorporate(vector< shared_ptr<VentureValue> >&,
                                shared_ptr<VentureValue>);
  virtual void Remove(vector< shared_ptr<VentureValue> >&,
                           shared_ptr<VentureValue>);

public:
  XRP__memoized_procedure();
  virtual void Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value); // Unsampler or sampler?
  virtual bool IsRandomChoice();
  virtual bool CouldBeRescored();
  virtual string GetName();
  
  weak_ptr<NodeXRPApplication> maker;
  shared_ptr<VentureValue> operator_value; // FIXME: VentureValue is not too ambiguous?
  map<string, XRP__memoizer_map_element> mem_table;
  size_t my_last_evaluation_id; // FIXME: describe.
};

#endif
