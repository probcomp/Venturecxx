#include "HeaderPre.h"
#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "Analyzer.h"
#include "XRPCore.h"
#include "RIPL.h"

RescorerResamplerResult::RescorerResamplerResult(shared_ptr<VentureValue> new_value,
                        real new_loglikelihood)
  : new_value(new_value),
    new_loglikelihood(new_loglikelihood)
{}
  
ReevaluationResult::ReevaluationResult(shared_ptr<VentureValue> passing_value,
                    bool pass_further)
  : passing_value(passing_value),
    pass_further(pass_further)
{}
  
ReevaluationEntry::ReevaluationEntry(shared_ptr<NodeEvaluation> reevaluation_node,
                  shared_ptr<NodeEvaluation> caller,
                  shared_ptr<VentureValue> passing_value,
                  size_t priority)
  : reevaluation_node(reevaluation_node),
    caller(caller),
    passing_value(passing_value),
    priority(priority)
{}
  
OmitPattern::OmitPattern(vector<size_t>& omit_pattern,
            vector<size_t>& stop_pattern)
  : omit_pattern(omit_pattern),
    stop_pattern(stop_pattern)
{}

ReevaluationParameters::ReevaluationParameters
(shared_ptr<NodeXRPApplication> principal_node,
 set<ReevaluationEntry,
     ReevaluationOrderComparer>& reevaluation_queue,
 stack< shared_ptr<Node> >& touched_nodes,
 vector< shared_ptr<Node> >& touched_nodes2,
 ProposalInfo& this_proposal,
 stack<OmitPattern>& omit_patterns)
  : __log_p_old(0.0),
    __log_p_new(0.0),
    __log_q_from_old_to_new(0.0),
    __log_q_from_new_to_old(0.0),
    __unsatisfied_constraint(false),
    principal_node(principal_node),
    
  reevaluation_queue(reevaluation_queue),
  touched_nodes(touched_nodes),
  touched_nodes2(touched_nodes2),
  this_proposal(this_proposal),
  omit_patterns(omit_patterns)
{}

shared_ptr<VentureValue>
XRP::Sample(vector< shared_ptr<VentureValue> >& arguments,
            shared_ptr<NodeXRPApplication> caller,
            EvaluationConfig& evaluation_config) {
  shared_ptr<VentureValue> new_sample;
  real loglikelihood;

  new_sample = Sampler(arguments, caller, evaluation_config);
  loglikelihood = GetSampledLoglikelihood(arguments, new_sample);
  evaluation_config.__log_unconstrained_score += loglikelihood;

  if (this->IsRandomChoice() == true) {
    if (evaluation_config.in_proposal == false) {
      AddToRandomChoices(dynamic_pointer_cast<NodeXRPApplication>(caller));
      //cout << "Adding a random choice" << endl;
    } else {
      evaluation_config.reevaluation_config_ptr->creating_random_choices.insert(dynamic_pointer_cast<NodeXRPApplication>(caller->shared_from_this()));
    }
  }
  
  //Debug// cout << "Incorporate from " << caller << endl;
  Incorporate(arguments, new_sample);

  if (evaluation_config.in_proposal == true) {
    if (this->GetName() == "XRP__memoized_procedure") {
      string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(arguments);
      XRP__memoizer_map_element& mem_table_element =
        (*(dynamic_pointer_cast<XRP__memoized_procedure>(this->shared_from_this())->mem_table.find(mem_table_key))).second;
      //cout << "active uses: " << mem_table_element.active_uses << " | " << evaluation_config.in_proposal << endl;
      if (mem_table_element.active_uses == 1 && mem_table_element.hidden_uses > 0) {
        UnabsorbBranchProbability(mem_table_element.application_caller_node, evaluation_config.reevaluation_config_ptr);
      }
    }
  }
  
  return new_sample;
}

shared_ptr<RescorerResamplerResult>
XRP::RescorerResampler(vector< shared_ptr<VentureValue> >& old_arguments,
                       vector< shared_ptr<VentureValue> >& new_arguments,
                       shared_ptr<NodeXRPApplication> caller,
                       bool forced_resampling,
                       shared_ptr<ReevaluationParameters> reevaluation_parameters,
                       EvaluationConfig& evaluation_config,
                       bool sampled_value_has_changed) {
  // This check slows the inference, though only by constant time.
  // Warning! If somebody wants to remove this *check*,
  // it is necessary to know that without it in some situtations there would be a problem:
  // Let's consider memoized procedure MP = (mem (lambda (id) (CRP))).
  // Let's also assume that CRP works in the way that it returns the least
  // non-negative free number in the case of a new table.
  // If we then have in the code (MP (flip)), without this *check*,
  // and flip reflips from *false* to *false*,
  // memoization node will lose output reference to call to (MP (flip)).
  // FIXME: (self-notice) Yura, do not forget to remove
  //        that the (if (flip) (lambda ...) (lambda ...))
  //        has been already disabled for reevaluation
  //        in another code part!
  bool arguments_are_different = false;
  for (size_t index = 0; index < old_arguments.size(); index++) {
    if (old_arguments[index]->GetType() != new_arguments[index]->GetType() || // FIXME: Will not work now with the current NIL-LIST implementation?
          old_arguments[index]->CompareByValue(new_arguments[index]) == false) {
      arguments_are_different = true;
      break;
    }
  }
  if (arguments_are_different == true) {
    if (XRP__memoized_procedure__MakeMapKeyFromArguments(old_arguments) == XRP__memoized_procedure__MakeMapKeyFromArguments(new_arguments)) {
      // throw std::runtime_error("This should not happen (arguments are different, but 'hash' function from them is not).");
    }
  }
  //cout << "Pam: " << arguments_are_different << " " << forced_resampling << " " << sampled_value_has_changed << " " << this->GetName() << endl;
  if (arguments_are_different == false && !forced_resampling && !sampled_value_has_changed) {
    Incorporate(new_arguments, caller->my_sampled_value);
    
    return shared_ptr<RescorerResamplerResult>(
      new RescorerResamplerResult(shared_ptr<VentureValue>(),
                                  0.0)); // Is it okay that we do not send the actual loglikelihood?
                                  // Added Jan/5/2013: Especially when we now do not cancel by default?
  }
  
  // Delete it?
  // assert(!CouldBeRescored() || !(GetSampledLoglikelihood(new_arguments, caller->my_sampled_value) == log(0.0)));

  if (forced_resampling || !CouldBeRescored()
        // || (GetSampledLoglikelihood(new_arguments, caller->my_sampled_value) == log(0.0))
        ) { // Resampling.

    shared_ptr<VentureValue> new_sample;
    if (this->IsRandomChoice() &&
          evaluation_config.reevaluation_config_ptr != shared_ptr<ReevaluationParameters>() &&
          evaluation_config.reevaluation_config_ptr->proposing_value_for_this_proposal != shared_ptr<VentureValue>()) {
      new_sample = evaluation_config.reevaluation_config_ptr->proposing_value_for_this_proposal;
      if (GetSampledLoglikelihood(new_arguments, new_sample) == log(0.0)) {
        reevaluation_parameters->__unsatisfied_constraint = true;
      }
      /*
      if (evaluation_config.reevaluation_config_ptr->forcing_not_collecting == false) {
        new_sample = Sampler(new_arguments, caller, evaluation_config);
        assert(evaluation_config.reevaluation_config_ptr->random_database->count(caller->node_key) == 0);
        (*(evaluation_config.reevaluation_config_ptr->random_database))[caller->node_key] = new_sample;
      } else {
        assert(evaluation_config.reevaluation_config_ptr->random_database->count(caller->node_key) == 1);
        new_sample = (*(evaluation_config.reevaluation_config_ptr->random_database))[caller->node_key];
      }
      */
    } else {
      new_sample = Sampler(new_arguments, caller, evaluation_config);
    }
    if (this->IsRandomChoice() == true) {
      assert(evaluation_config.in_proposal == true);
      reevaluation_parameters->creating_random_choices.insert(dynamic_pointer_cast<NodeXRPApplication>(caller));
    }
    real new_loglikelihood = GetSampledLoglikelihood(new_arguments, new_sample);

    evaluation_config.__log_unconstrained_score += new_loglikelihood;
    
    Incorporate(new_arguments, new_sample);
    
    if (this->GetName() == "XRP__memoized_procedure") {
      string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(new_arguments);
      XRP__memoizer_map_element& mem_table_element =
        (*(dynamic_pointer_cast<XRP__memoized_procedure>(this->shared_from_this())->mem_table.find(mem_table_key))).second;
      //cout << "active uses: " << mem_table_element.active_uses << " | " << evaluation_config.in_proposal << endl;
      if (mem_table_element.active_uses == 1 && mem_table_element.hidden_uses > 0) {
        UnabsorbBranchProbability(mem_table_element.application_caller_node, reevaluation_parameters);
      }
    }

    return shared_ptr<RescorerResamplerResult>(new RescorerResamplerResult(new_sample,
                                                                           new_loglikelihood)); // FIXME: This thing does nothing now, but it should work when mem would be implemented in the right way!
  } else { // Rescoring.
    // Rescoring:
    // 1) If arguments have changed.
    // 2) If operator has changed, but it is the same XRP type.
    if (this->IsRandomChoice() == true) {
      assert(evaluation_config.in_proposal == true);
      reevaluation_parameters->creating_random_choices.insert(dynamic_pointer_cast<NodeXRPApplication>(caller));
    }
    
    real new_loglikelihood = GetSampledLoglikelihood(new_arguments, caller->my_sampled_value);
    
    evaluation_config.__log_unconstrained_score += new_loglikelihood;
    
    Incorporate(new_arguments, caller->my_sampled_value);
    
    return shared_ptr<RescorerResamplerResult>(
      new RescorerResamplerResult(shared_ptr<VentureValue>(),
                                  0.0));
  }
}

XRP::XRP() {}
shared_ptr<VentureValue> XRP::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  throw std::runtime_error("It should not happen.");
} // Should be just ";"?
void XRP::Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value) {
  // By default it is blank function.
}
real XRP::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  throw std::runtime_error("It should not happen.");
} // Should be just ";"?
void XRP::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
  throw std::runtime_error("It should not happen.");
} // Should be just ";"?
void XRP::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
  throw std::runtime_error("It should not happen.");
} // Should be just ";"?
  
bool XRP::IsRandomChoice() { return false; }
bool XRP::CouldBeRescored() { return false; }
string XRP::GetName() { return "XRPClass"; }

bool XRP::CouldBeEnumerated() {
  return false;
}

bool XRP::CouldBeSliceSampled() {
  return false;
}

set< shared_ptr<VentureValue> > XRP::EnumeratingSupport() {
  throw std::runtime_error("Should not be called, because this XRP could not be enumerated.");
}
