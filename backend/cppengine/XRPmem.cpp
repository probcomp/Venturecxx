
#include "HeaderPre.h"
#include "XRPmem.h"

shared_ptr<VentureValue> XRP__memoizer::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  // Check that it is LAMBDA or XRPApplication.

  shared_ptr<XRP> new_xrp = shared_ptr<XRP>(new XRP__memoized_procedure());
  dynamic_pointer_cast<XRP__memoized_procedure>(new_xrp)->operator_value = arguments[0]; // Should be done on the line above through its constructor.
  dynamic_pointer_cast<XRP__memoized_procedure>(new_xrp)->maker = caller;
  return shared_ptr<VentureXRP>(new VentureXRP(new_xrp));
}

real XRP__memoizer::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0); // ?
}

void XRP__memoizer::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
}

void XRP__memoizer::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
}
bool XRP__memoizer::IsRandomChoice() { return false; }
bool XRP__memoizer::CouldBeRescored() { return false; }
string XRP__memoizer::GetName() { return "XRP__memoizer"; }






XRP__memoized_procedure::XRP__memoized_procedure()
  : my_last_evaluation_id(0)
{}

string XRP__memoized_procedure__MakeMapKeyFromArguments(vector< shared_ptr<VentureValue> >& arguments) {
  string arguments_strings = "(";
  for (size_t index = 0; index < arguments.size(); index++) {
    if (index != 0) { arguments_strings += " "; }
    arguments_strings += arguments[index]->GetString();
  }
  arguments_strings += ")";
  return arguments_strings;
}

shared_ptr<VentureValue> XRP__memoized_procedure::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(arguments);

  if (this->mem_table.count(mem_table_key) == 0) {
    // cout << "*** Creating the mem node " << mem_table_key << endl;
    shared_ptr<NodeSelfEvaluating> operator_node =
      shared_ptr<NodeSelfEvaluating>(new NodeSelfEvaluating(operator_value));
    vector< shared_ptr<NodeEvaluation> > operands_nodes;
    for (size_t index = 0; index < arguments.size(); index++) {
      operands_nodes.push_back(shared_ptr<NodeSelfEvaluating>(new NodeSelfEvaluating(arguments[index])));
    }
    shared_ptr<NodeApplicationCaller> application_caller =
      shared_ptr<NodeApplicationCaller>(new NodeApplicationCaller(operator_node, operands_nodes));
    
    this->mem_table.insert
      (pair<string, XRP__memoizer_map_element>(mem_table_key, XRP__memoizer_map_element(application_caller)));

    shared_ptr<VentureValue> result =
      Evaluator(this->mem_table[mem_table_key].application_caller_node,
                this->maker.lock()->environment, // FIXME: Is it okay?
                caller,
                this->maker.lock(), // FIXME: Is it okay?
                evaluation_config,
                mem_table_key);
  } else {
    // cout << "*** Restoring the mem node " << mem_table_key << endl;
    // Adding the output reference link by hand.
    this->mem_table[mem_table_key].application_caller_node
      ->output_references.insert(caller);
  }
  XRP__memoizer_map_element& mem_table_element =
    (*(this->mem_table.find(mem_table_key))).second;

  mem_table_element.hidden_uses++;
  //cout << "Returning (from mem): " << GetBranchValue(mem_table_element.application_caller_node)->GetString() << endl;
  return GetBranchValue(mem_table_element.application_caller_node);
}

void XRP__memoized_procedure::Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value) {
  string mem_table_key =
    XRP__memoized_procedure__MakeMapKeyFromArguments(old_arguments);
  if (this->mem_table.count(mem_table_key) == 0) {
    throw std::runtime_error("Cannot find the necessary key in the mem table.");
  }
  XRP__memoizer_map_element& mem_table_element =
    (*(this->mem_table.find(mem_table_key))).second;
  mem_table_element.application_caller_node->output_references.erase(mem_table_element.application_caller_node->output_references.find(caller));
  if (mem_table_element.hidden_uses == 0) {
    throw std::runtime_error("(1) Cannot do 'mem_table_element.hidden_uses--'.");
  }
  mem_table_element.hidden_uses--;
  if (mem_table_element.hidden_uses == 0 && mem_table_element.active_uses == 0) {
    this->mem_table.erase(mem_table_key);
  }
}

real XRP__memoized_procedure::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0); // ?
}

void XRP__memoized_procedure::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
  //Debug// assert(arguments.size() == 1);
  //Debug// cout << "Incorporating" << arguments[0]->GetString() << endl;

  string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(arguments);
  if (this->mem_table.count(mem_table_key) == 0) {
    throw std::runtime_error("Cannot find the necessary key in the mem table.");
  }
  XRP__memoizer_map_element& mem_table_element =
    (*(this->mem_table.find(mem_table_key))).second;
  if (mem_table_element.hidden_uses == 0) {
    stack< shared_ptr<Node> > tmp;
    DrawGraphDuringMH(tmp);
    throw std::runtime_error("(2) Cannot do 'mem_table_element.hidden_uses--'.");
  }
  mem_table_element.hidden_uses--;
  mem_table_element.active_uses++;
}

#include "RIPL.h" // For DrawGraphDuringMH. Delete after.

void XRP__memoized_procedure::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
  //Debug// assert(arguments.size() == 1);
  // cout << "Removing " << " " << this << " " << XRP__memoized_procedure__MakeMapKeyFromArguments(arguments) << endl;

  string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(arguments);
  if (this->mem_table.count(mem_table_key) == 0) {
    throw std::runtime_error("Cannot find the necessary key in the mem table.");
  }
  XRP__memoizer_map_element& mem_table_element =
    (*(this->mem_table.find(mem_table_key))).second;
  if (mem_table_element.active_uses == 0) {
    cout << "sizeof: " << global_reevaluation_parameters->touched_nodes.size() << endl;
    DrawGraphDuringMH(global_reevaluation_parameters->touched_nodes);
    throw std::runtime_error("Cannot do 'mem_table_element.active_uses--'.");
  }
  mem_table_element.hidden_uses++;
  mem_table_element.active_uses--;
}
bool XRP__memoized_procedure::IsRandomChoice() { return false; }
bool XRP__memoized_procedure::CouldBeRescored() { return false; }
string XRP__memoized_procedure::GetName() { return "XRP__memoized_procedure"; }
