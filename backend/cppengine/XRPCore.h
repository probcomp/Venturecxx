
#ifndef VENTURE___XRP_CORE_H
#define VENTURE___XRP_CORE_H

#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"

struct NodeXRPApplication;
extern set< weak_ptr<NodeXRPApplication> > random_choices;
extern vector< set< weak_ptr<NodeXRPApplication> >::iterator > random_choices_vector;
extern int next_gensym_atom;

struct RescorerResamplerResult {
  RescorerResamplerResult(shared_ptr<VentureValue>,
                          real);
  shared_ptr<VentureValue> new_value;
  real new_loglikelihood;
};

struct ReevaluationResult {
  ReevaluationResult(shared_ptr<VentureValue>,
                     bool);
  shared_ptr<VentureValue> passing_value;
  bool pass_further;
};

struct ReevaluationEntry {
  ReevaluationEntry(shared_ptr<NodeEvaluation> reevaluation_node,
                    shared_ptr<NodeEvaluation> caller,
                    shared_ptr<VentureValue> passing_value,
                    size_t priority);
  shared_ptr<NodeEvaluation> reevaluation_node;
  shared_ptr<NodeEvaluation> caller;
  shared_ptr<VentureValue> passing_value;
  size_t priority;
};

struct OmitPattern {
  OmitPattern(vector<size_t>&,
              vector<size_t>&);
  vector<size_t> omit_pattern;
  vector<size_t> stop_pattern; // stop_pattern is omit_pattern.pop().
                               // Use it in the future to increase efficiency,
                               // and make the code more accurate.
};

struct ReevaluationOrderComparer;
struct Node;
struct ProposalInfo;
struct OmitPattern;

struct ReevaluationParameters : public boost::enable_shared_from_this<ReevaluationParameters> {
  ReevaluationParameters
  (shared_ptr<NodeXRPApplication> principal_node,
   set<ReevaluationEntry,
       ReevaluationOrderComparer>& reevaluation_queue,
   stack< shared_ptr<Node> >& touched_nodes,
   vector< shared_ptr<Node> >& touched_nodes2,
   ProposalInfo& this_proposal,
   stack<OmitPattern>& omit_patterns);
  real __log_p_old;
  real __log_p_new;
  real __log_q_from_old_to_new;
  real __log_q_from_new_to_old;
  real __tmp_for_unconstrain;
  bool __unsatisfied_constraint;
  shared_ptr<NodeXRPApplication> principal_node;
  
  // For Enumeration:
  bool we_are_in_enumeration;
  shared_ptr<VentureValue> proposing_value_for_this_proposal;
  shared_ptr< map<string, shared_ptr<VentureValue> > > random_database;
  bool forcing_not_collecting;
  
  set<ReevaluationEntry,
      ReevaluationOrderComparer>& reevaluation_queue;
  stack< shared_ptr<Node> >& touched_nodes;
  vector< shared_ptr<Node> >& touched_nodes2;
  ProposalInfo& this_proposal;
  stack<OmitPattern>& omit_patterns;
  
  set< shared_ptr<NodeXRPApplication> > creating_random_choices;
  set< shared_ptr<NodeXRPApplication> > deleting_random_choices;
  
  map< shared_ptr<NodeXRPApplication>, shared_ptr<VentureValue> > new_values_for_memoized_procedures;
};

struct EvaluationConfig;
class XRP : public boost::enable_shared_from_this<XRP> {
public: // Should be private.
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >&,
                                       shared_ptr<VentureValue>);
  virtual void Incorporate(vector< shared_ptr<VentureValue> >&,
                                shared_ptr<VentureValue>);
  virtual void Remove(vector< shared_ptr<VentureValue> >&,
                           shared_ptr<VentureValue>);
                           
public:
  //XRP(shared_ptr<XRP> maker) : maker(maker) {}
  XRP();
  shared_ptr<VentureValue> Sample(vector< shared_ptr<VentureValue> >&, // FIXME: why not virtual?
                                  shared_ptr<NodeXRPApplication>,
                                  EvaluationConfig& evaluation_config);
 virtual void Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value); // Unsampler or sampler?
  shared_ptr<RescorerResamplerResult>
  RescorerResampler(vector< shared_ptr<VentureValue> >& old_arguments,
                    vector< shared_ptr<VentureValue> >& new_arguments,
                    shared_ptr<NodeXRPApplication> caller,
                    bool forced_resampling,
                    shared_ptr<ReevaluationParameters> reevaluation_parameters,
                    EvaluationConfig& evaluation_config,
                    bool sampled_value_has_changed);
  virtual bool IsRandomChoice();
  virtual bool CouldBeRescored();
  virtual string GetName();
  virtual bool CouldBeEnumerated();
  virtual bool CouldBeSliceSampled();
  virtual set< shared_ptr<VentureValue> > EnumeratingSupport();

public: // Should be private?
};

#endif
