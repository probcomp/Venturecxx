
#include "HeaderPre.h"
#include "Header.h"
#include "VentureValues.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "XRPmem.h"

shared_ptr<VentureValue> Evaluator(shared_ptr<NodeEvaluation> evaluation_node,
                                   shared_ptr<NodeEnvironment> environment,
                                   shared_ptr<Node> output_reference_target,
                                   shared_ptr<NodeEvaluation> caller,
                                   EvaluationConfig& evaluation_config,
                                   string request_postfix) {
  if (caller == shared_ptr<NodeEvaluation>()) { // It is directive.
    DIRECTIVE_COUNTER++;
    evaluation_node->node_key = boost::lexical_cast<string>(DIRECTIVE_COUNTER);
    evaluation_node->myorder.push_back(DIRECTIVE_COUNTER);
  } else {
    if (caller->GetNodeType() == DIRECTIVE_ASSUME ||
          caller->GetNodeType() == DIRECTIVE_PREDICT ||
          caller->GetNodeType() == DIRECTIVE_OBSERVE) {
      evaluation_node->node_key = caller->node_key + "|from_dir";
    } else if (caller->GetNodeType() == APPLICATION_CALLER) {
      shared_ptr<NodeApplicationCaller> parent_node = dynamic_pointer_cast<NodeApplicationCaller>(caller);
      if (parent_node->application_operator == evaluation_node) {
        evaluation_node->node_key = caller->node_key + "|op";
      } else if (request_postfix.substr(0, 5) == "args_") {
        evaluation_node->node_key = caller->node_key + "|" + request_postfix;
      } else if (parent_node->application_node == evaluation_node || parent_node->new_application_node == evaluation_node) {
        evaluation_node->node_key = caller->node_key + "|ap";
      } else {
        throw std::runtime_error("Unexpected situation for the 'node_key' (1).");
      }
    } else if (caller->GetNodeType() == XRP_APPLICATION &&
                 dynamic_pointer_cast<NodeXRPApplication>(caller)->xrp->xrp->GetName() == "XRP__memoizer") {
      assert(request_postfix != "");
      evaluation_node->node_key = caller->node_key + "|m:" + request_postfix;
    } else {
      throw std::runtime_error("Unexpected situation for the 'node_key' (2).");
    }

    evaluation_node->myorder = caller->myorder;
    if (caller->GetNodeType() == XRP_APPLICATION &&
          dynamic_pointer_cast<NodeXRPApplication>(caller)->xrp->xrp->GetName() == "XRP__memoizer" && 1 == 1)
    {
      size_t& my_last_evaluation_id =
        dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<VentureXRP>(
          dynamic_pointer_cast<NodeXRPApplication>(caller)->my_sampled_value)->xrp)->my_last_evaluation_id;
      my_last_evaluation_id++;
      // FIXME: lock things for multithread version?
      evaluation_node->myorder.push_back(my_last_evaluation_id); // (std::numeric_limits<size_t>::max());
    } else {
      caller->last_child_order++;
      evaluation_node->myorder.push_back(caller->last_child_order);
    }
    evaluation_node->parent = caller;
  }

  evaluation_node->environment = environment;
  if (output_reference_target != shared_ptr<Node>()) {
    evaluation_node->output_references.insert(output_reference_target);
  }

  if (evaluation_node->earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    // Potential recursion problem (i.e. stack overflow).
    // FIXME: in the future implement via the loop.
    Evaluator(evaluation_node->earlier_evaluation_nodes,
              environment,
              shared_ptr<Node>(),
              dynamic_pointer_cast<NodeEvaluation>(evaluation_node->shared_from_this()),
              evaluation_config,
              "..."); // FIXME: not supported!
  }

  assert(evaluation_node->evaluated == false);
  evaluation_node->evaluated = true; // Not too early?
  return evaluation_node->Evaluate(environment, evaluation_config);
}

shared_ptr<Node> BindToEnvironment(shared_ptr<NodeEnvironment> target_environment,
                                   shared_ptr<VentureSymbol> variable_name,
                                   shared_ptr<VentureValue> binding_value,
                                   shared_ptr<NodeEvaluation> binding_node) {
  if (target_environment->variables.count(variable_name->GetString()) != 0) {
    throw std::runtime_error(("Binding variable, which has been already bound: " + variable_name->GetString()).c_str());
  }
  target_environment->variables[variable_name->GetString()] =
    shared_ptr<NodeVariable>(new NodeVariable(target_environment, binding_value, binding_node));
  target_environment->variables[variable_name->GetString()]->weak_ptr_to_me = dynamic_pointer_cast<Node>(target_environment->variables[variable_name->GetString()]->shared_from_this()); // Silly.
  return target_environment->variables[variable_name->GetString()];
}

// Should be implemented with the function above?
void BindVariableToEnvironment(shared_ptr<NodeEnvironment> target_environment,
                               shared_ptr<VentureSymbol> variable_name,
                               shared_ptr<NodeVariable> binding_variable) {
  if (target_environment->variables.count(variable_name->GetString()) != 0) {
    throw std::runtime_error(("Binding variable, which has been already bound: " + variable_name->GetString()).c_str());
  }
  target_environment->variables[variable_name->GetString()] =
    binding_variable;
}

shared_ptr<VentureValue> LookupValue(shared_ptr<NodeEnvironment> environment,
                                     shared_ptr<VentureSymbol> variable_name,
                                     shared_ptr<NodeEvaluation> lookuper,
                                     bool old_values) { // = false, see the header
  shared_ptr<NodeEnvironment> inspecting_environment = environment;
  while (inspecting_environment != shared_ptr<NodeEnvironment>()) {
    if (inspecting_environment->variables.count(variable_name->GetString()) == 1) {
      if (lookuper != shared_ptr<NodeEvaluation>()) {
        if (lookuper->GetNodeType() == LOOKUP) {
          dynamic_pointer_cast<NodeLookup>(lookuper)->where_lookuped =
            inspecting_environment->variables[variable_name->GetString()];
        }
        if (inspecting_environment->variables[variable_name->GetString()]->output_references.count(lookuper) == 0) {
          // If there is no dependency yet:
            inspecting_environment->variables[variable_name->GetString()]->output_references.insert(lookuper);
        }
      }
      if (inspecting_environment->variables[variable_name->GetString()]->new_value == shared_ptr<VentureValue>() ||
          old_values == true) {
        // cout << ">>> Returning the old value " << inspecting_environment->variables[variable_name->GetString()]->value->GetString() << endl;
        return inspecting_environment->variables[variable_name->GetString()]->value;
      } else {
        // cout << ">>> Returning the new value " << inspecting_environment->variables[variable_name->GetString()]->new_value->GetString() << endl;
        return inspecting_environment->variables[variable_name->GetString()]->new_value;
      }
    } else {
      inspecting_environment = inspecting_environment->parent_environment.lock();
    }
  }
  //cout << "Error: " << variable_name->GetString() << endl;
  throw std::runtime_error((string("Unbound variable: ") + variable_name->GetString()).c_str());
}

shared_ptr<VentureValue> LookupValue(shared_ptr<NodeEnvironment> environment,
                                     size_t index,
                                     shared_ptr<NodeEvaluation> lookuper,
                                     bool old_values) { // = false, see the header
  if (index >= environment->local_variables.size()) {
    throw std::runtime_error("LookupValue: out of bound.");
  }
  if (lookuper != shared_ptr<NodeEvaluation>()) {
    if (lookuper->GetNodeType() == LOOKUP) {
      dynamic_pointer_cast<NodeLookup>(lookuper)->where_lookuped =
        environment->local_variables[index];
    }
    if (environment->local_variables[index]->output_references.count(lookuper) == 0) {
      // If there is no dependency yet:
      environment->local_variables[index]->output_references.insert(lookuper);
    }
  }
  if (environment->local_variables[index]->new_value == shared_ptr<VentureValue>() ||
      old_values == true) {
    // cout << ">>> Returning the old value " << environment->local_variables[index]->value << endl;
    return environment->local_variables[index]->value;
  } else {
    // cout << ">>> Returning the new value " << environment->local_variables[index]->new_value << endl;
    return environment->local_variables[index]->new_value;
  }
}

shared_ptr<NodeEvaluation> FindConstrainingNode(shared_ptr<Node> node, int delta, bool if_old_arguments) {
  while (true) {
    assert(node != shared_ptr<Node>());
    assert(static_cast<int>(node->constraint_times) + delta >= 0);
    node->constraint_times += delta;
    if (node->GetNodeType() == LOOKUP) {
      node = dynamic_pointer_cast<NodeLookup>(node)->where_lookuped.lock();
      continue;
    } else if (node->GetNodeType() == VARIABLE) {
      node = dynamic_pointer_cast<NodeVariable>(node)->binding_node.lock();
      continue;
    } else if (node->GetNodeType() == APPLICATION_CALLER) {
      if (dynamic_pointer_cast<NodeApplicationCaller>(node)->new_application_node != shared_ptr<NodeEvaluation>()) {
        node = dynamic_pointer_cast<NodeApplicationCaller>(node)->new_application_node;
      } else {
        node = dynamic_pointer_cast<NodeApplicationCaller>(node)->application_node;
      }
      continue;
    } else if (node->GetNodeType() == SELF_EVALUATING) {
      return dynamic_pointer_cast<NodeEvaluation>(node);
    } else if (node->GetNodeType() == XRP_APPLICATION) {
      if (dynamic_pointer_cast<NodeXRPApplication>(node)->xrp->xrp->GetName() == "XRP__memoized_procedure") {
        vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(dynamic_pointer_cast<NodeXRPApplication>(node)->environment, // Not efficient?
                                        dynamic_pointer_cast<NodeEvaluation>(node),
                                        if_old_arguments);
        string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(got_arguments);
        if (dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<NodeXRPApplication>(node)->xrp->xrp)->mem_table.count(mem_table_key) == 0) {
          throw std::runtime_error("Cannot find the necessary key in the mem table.");
        }
        XRP__memoizer_map_element& mem_table_element =
          (*(dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<NodeXRPApplication>(node)->xrp->xrp)->mem_table.find(mem_table_key))).second;
        return FindConstrainingNode(mem_table_element.application_caller_node, delta, if_old_arguments);
      } else {
        return dynamic_pointer_cast<NodeEvaluation>(node);
      }
    } else if (node->GetNodeType() == LAMBDA_CREATOR) {
      return shared_ptr<NodeEvaluation>();
    } else {
      throw std::runtime_error("Cannot find the node for potential constraining. Unexpected node type.");
    }
  }
}

ConstrainingResult ConstrainBranch(shared_ptr<NodeEvaluation> toppest_branch_node, shared_ptr<VentureValue> desired_value, shared_ptr<ReevaluationParameters> reevaluation_parameters, size_t constraint_times) {
  shared_ptr<NodeEvaluation> constraining_node = FindConstrainingNode(toppest_branch_node, constraint_times, false);

  //cout << "toppest_branch_node node: " << toppest_branch_node << endl;
  //cout << "Constraining node: " << constraining_node << endl;
  
  if (constraining_node->constraint_times == constraint_times && // "== constraint_times", not "== 0", because we just have already constraint it once!
        constraining_node->GetNodeType() == XRP_APPLICATION &&
        dynamic_pointer_cast<NodeXRPApplication>(constraining_node)->xrp->xrp->IsRandomChoice()) {
    if (reevaluation_parameters->creating_random_choices.count(dynamic_pointer_cast<NodeXRPApplication>(constraining_node)) == 1) {
      reevaluation_parameters->creating_random_choices.erase(dynamic_pointer_cast<NodeXRPApplication>(constraining_node));
    } else {
      reevaluation_parameters->deleting_random_choices.insert(dynamic_pointer_cast<NodeXRPApplication>(constraining_node));
    }
  }

  if (constraining_node->GetNodeType() == SELF_EVALUATING) {
    shared_ptr<NodeSelfEvaluating> node2 = dynamic_pointer_cast<NodeSelfEvaluating>(constraining_node);
    if (CompareValue(node2->value, desired_value)) {
      return CONSTRAININGRESULT_ALREADY_PROPER_VALUE;
    } else {
      reevaluation_parameters->__unsatisfied_constraint = true;
      return CONSTRAININGRESULT_CANNOT_CONSTRAIN;
    }
  } else if (constraining_node->GetNodeType() == XRP_APPLICATION) {
    shared_ptr<NodeXRPApplication> node2 = dynamic_pointer_cast<NodeXRPApplication>(constraining_node);
    //cout << "Current: " << node2->my_sampled_value->GetString() << " VS Desired: " << desired_value->GetString() << endl;
    if (CompareValue(node2->my_sampled_value, desired_value)) {
      return CONSTRAININGRESULT_ALREADY_PROPER_VALUE;
    } else {
      if (node2->constraint_times > constraint_times) { // "> constraint_times", not "> 0", because we just have already constraint it once!
        reevaluation_parameters->__unsatisfied_constraint = true;
        return CONSTRAININGRESULT_CANNOT_CONSTRAIN; // The already forced value is not the value we want. Rejecting.
      } else {
        if (!node2->xrp->xrp->CouldBeRescored()) {
          reevaluation_parameters->__unsatisfied_constraint = true;
          return CONSTRAININGRESULT_CANNOT_CONSTRAIN;
        }
        vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(node2->environment, // Not efficient?
                                        node2,
                                        false);
        node2->xrp->xrp->Remove(got_arguments, node2->my_sampled_value);
        //real logscore_change = -1.0 * node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
        // Assuming that if it was rescored, it saved the necessary value, i.e. there would not be necessity in
        // the forcing. Otherwise:
        reevaluation_parameters->__log_q_from_old_to_new -= node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
        reevaluation_parameters->__log_p_new -= node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
        node2->my_sampled_value = desired_value;
        reevaluation_parameters->__log_p_new += node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
        //logscore_change +=node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
        node2->xrp->xrp->Incorporate(got_arguments, node2->my_sampled_value);

        shared_ptr<ReevaluationResult> reevaluation_result =
          shared_ptr<ReevaluationResult>(
            new ReevaluationResult(desired_value, true));

        ReevaluationEntry current_reevaluation(node2, shared_ptr<NodeEvaluation>(), shared_ptr<VentureValue>(), REEVALUATION_PRIORITY__STANDARD);
        
        AddToReevaluationQueue(current_reevaluation, reevaluation_result, reevaluation_parameters);
        // FIXME: for multicore we just should add to the propagation queue this node also,
        //        to be sure that it does not participate in another proposal.
        //        Also there would be necessary to think what to do if
        //        the location of this node is "less" then location of any previously
        //        touched node during MH.
        return CONSTRAININGRESULT_VALUE_HAS_BEEN_CHANGED;
      }
    }
  } else {
    throw std::runtime_error("Cannot force with the provided observed value. Unexpected node type.");
  }
}

shared_ptr<VentureValue> UnconstrainBranch(shared_ptr<NodeEvaluation> node, size_t constraint_times, shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  shared_ptr<NodeEvaluation> potentially_constraint_node = FindConstrainingNode(node, -1 * static_cast<int>(constraint_times), true);
  if (potentially_constraint_node->constraint_times == 0 &&
        potentially_constraint_node->GetNodeType() == XRP_APPLICATION &&
        dynamic_pointer_cast<NodeXRPApplication>(potentially_constraint_node)->xrp->xrp->IsRandomChoice()) {
    shared_ptr<NodeXRPApplication> node2 = dynamic_pointer_cast<NodeXRPApplication>(potentially_constraint_node);
    vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(node2->environment, // Not efficient?
                                    node2,
                                    true);
    if (reevaluation_parameters == shared_ptr<ReevaluationParameters>()) {
      AddToRandomChoices(dynamic_pointer_cast<NodeXRPApplication>(potentially_constraint_node));
    } else {
      // Imporant, because we work as follows:
      // 1) Unconstrain.
      // 2) Absorb.
      // 3) Evaluate.
      // 4) Constrain.
      reevaluation_parameters->__tmp_for_unconstrain -= node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, node2->my_sampled_value);
      reevaluation_parameters->creating_random_choices.insert(dynamic_pointer_cast<NodeXRPApplication>(potentially_constraint_node));
    }
  }
  if (potentially_constraint_node->GetNodeType() == SELF_EVALUATING) {
    return dynamic_pointer_cast<NodeSelfEvaluating>(potentially_constraint_node)->value;
  } else if (potentially_constraint_node->GetNodeType() == XRP_APPLICATION) {
    return dynamic_pointer_cast<NodeXRPApplication>(potentially_constraint_node)->my_sampled_value;
  } else {
    throw std::runtime_error("Strange 'potentially_constraint_node->GetNodeType()'.");
  }
}

shared_ptr<VentureValue> GetBranchValue(shared_ptr<Node> node) {
  while (true) {
    assert(node != shared_ptr<Node>());
    if (node->GetNodeType() == LOOKUP) {
      node = dynamic_pointer_cast<NodeLookup>(node)->where_lookuped.lock();
      continue;
    } else if (node->GetNodeType() == VARIABLE) {
      return dynamic_pointer_cast<NodeVariable>(node)->GetCurrentValue();
      continue;
    } else if (node->GetNodeType() == APPLICATION_CALLER) {
      if (dynamic_pointer_cast<NodeApplicationCaller>(node)->new_application_node != shared_ptr<NodeEvaluation>()) {
        node = dynamic_pointer_cast<NodeApplicationCaller>(node)->new_application_node;
      } else {
        node = dynamic_pointer_cast<NodeApplicationCaller>(node)->application_node;
      }
      continue;
    } else if (node->GetNodeType() == SELF_EVALUATING) {
      return dynamic_pointer_cast<NodeSelfEvaluating>(node)->value;
    } else if (node->GetNodeType() == XRP_APPLICATION) {
      return dynamic_pointer_cast<NodeXRPApplication>(node)->my_sampled_value;
    } else if (node->GetNodeType() == LAMBDA_CREATOR) {
      return dynamic_pointer_cast<NodeLambdaCreator>(node)->returned_value;
    } else {
      throw std::runtime_error("Cannot get the branch value. Unexpected node type.");
    }
  }
}
