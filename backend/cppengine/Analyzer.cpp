#include "HeaderPre.h"
#include "Header.h"
#include "VentureParser.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "XRPCore.h"
#include "XRPmem.h"
#include "RIPL.h"
#include "MHProposal.h"

string GetNodeTypeAsString(size_t node_type) {
  switch (node_type) {
  case UNDEFINED_NODE:
    return "UNDEFINED_NODE";
  case ENVIRONMENT:
    return "ENVIRONMENT";
  case VARIABLE:
    return "VARIABLE";
  case UNDEFINED_EVALUATION_NODE:
    return "UNDEFINED_EVALUATION_NODE";
  case DIRECTIVE_ASSUME:
    return "DIRECTIVE_ASSUME";
  case DIRECTIVE_PREDICT:
    return "DIRECTIVE_PREDICT";
  case DIRECTIVE_OBSERVE:
    return "DIRECTIVE_OBSERVE";
  case SELF_EVALUATING:
    return "SELF_EVALUATING";
  case LAMBDA_CREATOR:
    return "LAMBDA_CREATOR";
  case LOOKUP:
    return "LOOKUP";
  case APPLICATION_CALLER:
    return "APPLICATION_CALLER";
  case XRP_APPLICATION:
    return "XRP_APPLICATION";
  default:
    throw std::runtime_error("Undefined node type.");
  }
}

string Node::GetContent() {
  return "";
}
string NodeSelfEvaluating::GetContent() {
  return this->value->GetString();
}
string NodeLookup::GetContent() {
  return this->symbol->symbol;
}

string Node::GetUniqueID() {
  return boost::lexical_cast<string>(this);
}

Node::Node()
  : was_deleted(false),
    constraint_times(0),
    _marked(false),
    already_absorbed(-1)
{
  //unique_id = ++NEXT_UNIQUE_ID; // FIXME: make transaction free!
}

// Destructors
/*
Node::~Node() { cout << "Deleting: Node" << endl; }
NodeEnvironment::~NodeEnvironment() { cout << "Deleting: NodeEnvironment" << endl; }
NodeVariable::~NodeVariable() { cout << "Deleting: NodeVariable" << endl; }
NodeEvaluation::~NodeEvaluation() { cout << "Deleting: NodeEvaluation" << endl; }
NodeDirectiveAssume::~NodeDirectiveAssume() { cout << "Deleting: NodeDirectiveAssume" << endl; }
NodeDirectivePredict::~NodeDirectivePredict() { cout << "Deleting: NodeDirectivePredict" << endl; }
NodeDirectiveObserve::~NodeDirectiveObserve() { cout << "Deleting: NodeDirectiveObserve" << endl; }
NodeSelfEvaluating::~NodeSelfEvaluating() { cout << "Deleting: NodeSelfEvaluating" << endl; }
NodeLambdaCreator::~NodeLambdaCreator() { cout << "Deleting: NodeLambdaCreator" << endl; }
NodeLookup::~NodeLookup() { cout << "Deleting: NodeLookup" << endl; }
NodeApplicationCaller::~NodeApplicationCaller() { cout << "Deleting: NodeApplicationCaller" << endl; }
NodeXRPApplication::~NodeXRPApplication() { cout << "Deleting: NodeXRPApplication" << endl; }
*/
Node::~Node() { this->DeleteNode(); }
NodeEnvironment::~NodeEnvironment() { this->DeleteNode(); }
NodeVariable::~NodeVariable() { this->DeleteNode(); }
NodeEvaluation::~NodeEvaluation() { this->DeleteNode(); }
NodeDirectiveAssume::~NodeDirectiveAssume() { this->DeleteNode(); }
NodeDirectivePredict::~NodeDirectivePredict() { this->DeleteNode(); }
NodeDirectiveObserve::~NodeDirectiveObserve() { this->DeleteNode(); }
NodeSelfEvaluating::~NodeSelfEvaluating() { this->DeleteNode(); }
NodeLambdaCreator::~NodeLambdaCreator() { this->DeleteNode(); }
NodeLookup::~NodeLookup() { this->DeleteNode(); }
NodeApplicationCaller::~NodeApplicationCaller() { this->DeleteNode(); }
NodeXRPApplication::~NodeXRPApplication() { this->DeleteNode(); }

VentureDataTypes Node::GetType() { return NODE; }
NodeTypes Node::GetNodeType() { return UNDEFINED_NODE; }
void Node::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  throw std::runtime_error("Should not be called (3).");
};

void Node::DeleteNode() {
  assert(this->was_deleted == false);
  this->was_deleted = true;
}



NodeEnvironment::NodeEnvironment(shared_ptr<NodeEnvironment> parent_environment)
  : parent_environment(parent_environment) {}
NodeTypes NodeEnvironment::GetNodeType() { return ENVIRONMENT; }

NodeVariable::NodeVariable(shared_ptr<NodeEnvironment> parent_environment, shared_ptr<VentureValue> value, weak_ptr<NodeEvaluation> binding_node)
  : parent_environment(parent_environment),
    value(value),
    new_value(shared_ptr<VentureValue>()),
    binding_node(binding_node)
{}
shared_ptr<VentureValue> NodeVariable::GetCurrentValue() {
  // FIXME for multicore:
  // 1) This function should be used anywhere instead of ...->some_variable->value;
  // 2) This function should check that the this->new_value is not provided
  //    by another MHProposal on another thread.
  if (this->new_value != shared_ptr<VentureValue>()) {
    return this->new_value;
  } else {
    return this->value;
  }
}
NodeTypes NodeVariable::GetNodeType() { return VARIABLE; }

void NodeVariable::DeleteNode() {
  if (this->binding_node.expired() == false) { // If it is not the global environment's initially bound variable?
    assert(this->binding_node.lock()->output_references.count(this->weak_ptr_to_me) == 1);
    this->binding_node.lock()->output_references.erase(this->binding_node.lock()->output_references.find(this->weak_ptr_to_me));
  }
}

NodeEvaluation::NodeEvaluation()
  : environment(shared_ptr<NodeEnvironment>()),
    earlier_evaluation_nodes(shared_ptr<NodeEvaluation>()),
    evaluated(false),
    last_child_order(0),
    parent(shared_ptr<NodeEvaluation>())
{}
NodeTypes NodeEvaluation::GetNodeType() { return UNDEFINED_EVALUATION_NODE; }
shared_ptr<NodeEvaluation> NodeEvaluation::clone() const {
  // Using the "clone pattern" in order to clone the Node for the lambda application.
  // See details here: http://www.cplusplus.com/forum/articles/18757/
  return shared_ptr<NodeEvaluation>(new NodeEvaluation());
}

void NodeEvaluation::DeleteNode() {

}

bool ReevaluationOrderComparer::operator()(const ReevaluationEntry& first, const ReevaluationEntry& second) {
  if (first.reevaluation_node->myorder.size() == 0) {
    throw std::runtime_error("The first node has not been evaluated yet!");
  }
  if (second.reevaluation_node->myorder.size() == 0) {
    throw std::runtime_error("The second node has not been evaluated yet!");
  }
  for (size_t index = 0; true; index++) {
    if (index >= first.reevaluation_node->myorder.size() &&
        index >= second.reevaluation_node->myorder.size()) {
      // Same orders.
      return (first.priority > second.priority);
      // The higher priority number (size_t), the lower the priority.
      // Therefore the priority = 0 is the highest.
    } else {
      if (index >= first.reevaluation_node->myorder.size()) {
        return true; // The first should be reevaluated later than the second.
      } else {
        if (index >= second.reevaluation_node->myorder.size()) {
          return false; // The first should be reevaluated earlier than the second.
        } else {
          if (first.reevaluation_node->myorder[index] == second.reevaluation_node->myorder[index]) {
            continue;
          } else {
            return (first.reevaluation_node->myorder[index] > second.reevaluation_node->myorder[index]);
          }
        }
      }
    }
  }
}
























NodeTypes NodeDirectiveAssume::GetNodeType() { return DIRECTIVE_ASSUME; }
NodeDirectiveAssume::NodeDirectiveAssume(shared_ptr<VentureSymbol> name, shared_ptr<NodeEvaluation> expression)
  : name(name), expression(expression) {}
void NodeDirectiveAssume::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
  assert(expression.get() != 0);
  processing_queue.push(expression);
};

void NodeDirectiveAssume::DeleteNode() {

}








NodeTypes NodeDirectivePredict::GetNodeType() { return DIRECTIVE_PREDICT; }
NodeDirectivePredict::NodeDirectivePredict(shared_ptr<NodeEvaluation> expression)
  : expression(expression) {}
void NodeDirectivePredict::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
  assert(expression.get() != 0);
  processing_queue.push(expression);
};

void NodeDirectivePredict::DeleteNode() {

}


















NodeTypes NodeDirectiveObserve::GetNodeType() { return DIRECTIVE_OBSERVE; }
NodeDirectiveObserve::NodeDirectiveObserve(shared_ptr<NodeEvaluation> expression, shared_ptr<VentureValue> observed_value)
  : expression(expression), observed_value(observed_value) {}
void NodeDirectiveObserve::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
  assert(expression.get() != 0);
  processing_queue.push(expression);
}

void NodeDirectiveObserve::DeleteNode() {

}















NodeTypes NodeSelfEvaluating::GetNodeType() { return SELF_EVALUATING; }
NodeSelfEvaluating::NodeSelfEvaluating(shared_ptr<VentureValue> value)
  : value(value) {}
shared_ptr<NodeEvaluation> NodeSelfEvaluating::clone() const {
  shared_ptr<NodeEvaluation> new_node = shared_ptr<NodeSelfEvaluating>(new NodeSelfEvaluating(this->value));
  new_node->comment = this->comment;
  return new_node;
}
void NodeSelfEvaluating::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
};

void NodeSelfEvaluating::DeleteNode() {

}













NodeTypes NodeLambdaCreator::GetNodeType() { return LAMBDA_CREATOR; }
NodeLambdaCreator::NodeLambdaCreator(shared_ptr<VentureList> arguments, shared_ptr<NodeEvaluation> expressions)
  : arguments(arguments), expressions(expressions) {

}
shared_ptr<NodeEvaluation> NodeLambdaCreator::clone() const {
  shared_ptr<NodeEvaluation> new_node = shared_ptr<NodeLambdaCreator>(new NodeLambdaCreator(this->arguments, this->expressions->clone()));
  new_node->comment = this->comment;
  return new_node;
}
void NodeLambdaCreator::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
  assert(expressions.get() != 0);
  processing_queue.push(expressions);
};
// Using standard copy constructor.

void NodeLambdaCreator::DeleteNode() {

}




NodeTypes NodeLookup::GetNodeType() { return LOOKUP; }
NodeLookup::NodeLookup(shared_ptr<VentureSymbol> symbol)
  : symbol(symbol) {}
shared_ptr<NodeEvaluation> NodeLookup::clone() const {
  shared_ptr<NodeLookup> new_lookup_node = shared_ptr<NodeLookup>(new NodeLookup(this->symbol));
  new_lookup_node->weak_ptr_to_me = dynamic_pointer_cast<NodeLookup>(new_lookup_node->shared_from_this());
  new_lookup_node->comment = this->comment;
  return new_lookup_node;
}
void NodeLookup::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
};

void NodeLookup::DeleteNode() {
  if (this->evaluated == true) {
    if (this->where_lookuped.expired() == false) { // FIXME: using "expired" here is not conceptually correct. Here we check if where_lookuped == weak_ptr<...>(). How to check it better?
      assert(this->where_lookuped.lock()->output_references.count(this->weak_ptr_to_me) == 1);
      this->where_lookuped.lock()->output_references.erase(this->where_lookuped.lock()->output_references.find(this->weak_ptr_to_me));
    } else {
      // Otherwise it means that we throw an exception when there is no bound variable.
      //
      // It is not good solution. Maybe, evaluated == true should be only when the node has been really evaluated?
    }
  }
}






NodeTypes NodeApplicationCaller::GetNodeType() { return APPLICATION_CALLER; }
NodeApplicationCaller::NodeApplicationCaller(shared_ptr<NodeEvaluation> application_operator,
                      vector< shared_ptr<NodeEvaluation> >& application_operands)
  : saved_evaluated_operator(shared_ptr<VentureValue>()),
    proposing_evaluated_operator(shared_ptr<VentureValue>()),
    application_operator(application_operator),
    application_operands(application_operands),
    MH_made_action(MH_ACTION__EMPTY_STATUS)
{}
shared_ptr<NodeEvaluation> NodeApplicationCaller::clone() const {
  vector< shared_ptr<NodeEvaluation> > empty_vector; // Remove it.
  shared_ptr<NodeApplicationCaller> NodeApplicationCaller_new =
    shared_ptr<NodeApplicationCaller>
      (new NodeApplicationCaller(shared_ptr<NodeEvaluation>(),
                                 empty_vector));
  NodeApplicationCaller_new->application_operator =
    shared_ptr<NodeEvaluation>(application_operator->clone());
  for (size_t index = 0; index < application_operands.size(); index++) {
    NodeApplicationCaller_new->application_operands.push_back(
      shared_ptr<NodeEvaluation>(application_operands[index]->clone()));
  }
  NodeApplicationCaller_new->comment = this->comment;
  return NodeApplicationCaller_new;
}
void NodeApplicationCaller::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
  assert(application_operator.get() != 0);
  processing_queue.push(application_operator);
  for (size_t index = 0; index < application_operands.size(); index++) {
    assert(application_operands[index].get() != 0);
    processing_queue.push(application_operands[index]);
  }
  if (this->evaluated == true) { // Is it right?
    if (application_node.get() == 0 && false) {
      stack< shared_ptr<Node> > tmp;
      tmp.push(dynamic_pointer_cast<Node>(this->shared_from_this()));
      //cout << this->evaluated << endl;
      assert(false);
      DrawGraphDuringMH(tmp);
      assert(false);
    }
    //assert(application_node.get() != 0);
    if (absorbing_parameter == 0) {
      if (application_node.get() != 0) {
        processing_queue.push(application_node);
      }
    }
    if (absorbing_parameter == 1) { // Absorbing.
      if (new_application_node.get() != 0) {
        processing_queue.push(new_application_node);
      } else if (application_node.get() != 0) {
        processing_queue.push(application_node);
      }
    }
    if (absorbing_parameter == 2) {
      if (new_application_node.get() != 0 && new_application_node->already_absorbed == MHid) {
        processing_queue.push(new_application_node);
      } else if (application_node.get() != 0 && application_node->already_absorbed == MHid) {
        processing_queue.push(application_node);
      } else {
        // throw std::runtime_error("Unabsorbing, but cannot find absorbed node.");
      }
    }
  }
};

void NodeApplicationCaller::DeleteNode() {

}






NodeTypes NodeXRPApplication::GetNodeType() { return XRP_APPLICATION; }
NodeXRPApplication::NodeXRPApplication(shared_ptr<VentureXRP> xrp)
  : xrp(xrp)
{}
// It should not have clone() method?
void NodeXRPApplication::GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter) {
  if (earlier_evaluation_nodes != shared_ptr<NodeEvaluation>()) {
    processing_queue.push(earlier_evaluation_nodes);
  }
};

void NodeXRPApplication::DeleteNode() {
  assert(this->xrp != shared_ptr<VentureXRP>() &&
           this->xrp->xrp != shared_ptr<XRP>());
  
  assert(!(weak_ptr_to_me._empty())); // FIXME: Only Boost thing?

  // FIXME: GetArgumentsFromEnvironment should be called without adding lookup references!
  vector< shared_ptr<VentureValue> > old_arguments = GetArgumentsFromEnvironment(this->environment, // Not efficient?
                                  shared_ptr<NodeEvaluation>(), // Are we sure that we have not deleted yet lookup links?
                                  true); // FIXME: we should be sure that we are receiving old arguments!

  this->xrp->xrp->
    Remove(old_arguments, this->my_sampled_value);
  
  this->xrp->xrp->Unsampler(old_arguments, this->weak_ptr_to_me, this->my_sampled_value);

  if (this->xrp->xrp->IsRandomChoice() == true) {
    DeleteRandomChoices(this->weak_ptr_to_me, this->location_in_random_choices);
  }
}




shared_ptr<NodeEvaluation> AnalyzeExpressions(shared_ptr<VentureList> expressions) {
  shared_ptr<NodeEvaluation> last_expression = shared_ptr<NodeEvaluation>();
  do {
    shared_ptr<NodeEvaluation> current_expression = AnalyzeExpression(GetFirst(expressions));
    expressions = GetNext(expressions);
    if (last_expression != shared_ptr<NodeEvaluation>()) {
      current_expression->earlier_evaluation_nodes = last_expression;
    }
    last_expression = current_expression;
  } while (expressions->GetType() != NIL);
  return last_expression;
}

shared_ptr<NodeEvaluation> AnalyzeExpression(shared_ptr<VentureValue> expression) {
  if (expression->GetType() == BOOLEAN ||
      expression->GetType() == COUNT ||
      expression->GetType() == REAL ||
      expression->GetType() == PROBABILITY ||
      expression->GetType() == ATOM ||
      expression->GetType() == SIMPLEXPOINT ||
      expression->GetType() == SMOOTHEDCOUNT ||
      expression->GetType() == NIL ||
      expression->GetType() == STRING) // As in Scheme and Lisp?.
  {
    shared_ptr<NodeEvaluation> new_self_evaluation = shared_ptr<NodeEvaluation>(new NodeSelfEvaluating(expression));
    new_self_evaluation->comment = expression->GetString();
    return new_self_evaluation;
  } else if (expression->GetType() == SYMBOL) {
    shared_ptr<NodeLookup> new_lookup_node = shared_ptr<NodeLookup>(new NodeLookup(ToVentureSymbol(expression)));
    new_lookup_node->weak_ptr_to_me = dynamic_pointer_cast<NodeLookup>(new_lookup_node->shared_from_this());
    new_lookup_node->comment = expression->GetString();
    return new_lookup_node;
  } else if (expression->GetType() == LIST) { // What about NIL? Change this comparison by IsList()?..
                                              //                                        (which returns
                                              //                                         'true' also for
                                              //                                         NIL)
    shared_ptr<VentureList> expression_list = ToVentureList(expression);
    if (CompareValue(GetFirst(expression_list), shared_ptr<VentureValue>(new VentureSymbol("quote")))) { // FIXME: without matching case?
      shared_ptr<NodeEvaluation> new_self_evaluation = shared_ptr<NodeEvaluation>(new NodeSelfEvaluating(GetNth(expression_list, 2)));
      new_self_evaluation->comment = GetNth(expression_list, 2)->GetString();
      return new_self_evaluation;
    } else if (CompareValue(GetFirst(expression_list), shared_ptr<VentureValue>(new VentureSymbol("if")))) {
      throw std::runtime_error("The 'if' sugar should be processed with the Python.");
      // Previous processing C++ code could be found here:
      // https://github.com/perov/Venture/blob/f67f9f36a9c5c3320403a2993ad5a57b32ed9cb5/src/Analyzer.cpp#L478
    } else if (CompareValue(GetFirst(expression_list), shared_ptr<VentureValue>(new VentureSymbol("lambda")))) {
      shared_ptr<NodeEvaluation> new_lambda_content_node =
        shared_ptr<NodeEvaluation>(
               new NodeLambdaCreator(ToVentureList(GetNth(expression_list, 2)),
                                     AnalyzeExpressions(GetNext(GetNext(expression_list)))));
      new_lambda_content_node->comment = expression_list->GetString();
      return new_lambda_content_node;
    } else {
      shared_ptr<VentureList> arguments_expressions = ToVentureList(GetNext(expression_list));
      vector< shared_ptr<NodeEvaluation> > arguments;
      while (GetFirst(arguments_expressions)->GetType() != NIL) {
        arguments.push_back(AnalyzeExpression(GetFirst(arguments_expressions)));
        arguments_expressions = arguments_expressions->cdr;
      }
      shared_ptr<NodeEvaluation> new_application_node =
        shared_ptr<NodeEvaluation>(
          new NodeApplicationCaller(AnalyzeExpression(GetFirst(expression_list)),
                                    arguments));
      new_application_node->comment = expression_list->GetString();
      return new_application_node;
    }
  } else {
    throw std::runtime_error("Undefined expression.");
  }
}

void NodeEnvironment::DeleteNode() {

}

shared_ptr<VentureValue>
NodeEvaluation::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) { // It seems we do not need this function, do we?
  throw std::runtime_error("It should not happen.");
}

shared_ptr<VentureValue>
NodeDirectiveAssume::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  this->my_value =              Evaluator(this->expression,
                                environment,
                                dynamic_pointer_cast<Node>(this->shared_from_this()),
                                dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()),
                                evaluation_config,
                                "");
  this->output_references.insert(
    BindToEnvironment(environment,
                      this->name,
                      this->my_value,
                      this->expression));
  return NIL_INSTANCE; // Something wiser?
}

shared_ptr<VentureValue>
NodeDirectivePredict::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
   this->my_value =
         Evaluator(this->expression,
                   environment,
                   dynamic_pointer_cast<Node>(this->shared_from_this()),
                   dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()),
                   evaluation_config,
                   "");
   //cout << this->my_value->GetString() << "$" << endl;
   return this->my_value;
}

shared_ptr<VentureValue>
NodeDirectiveObserve::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  Evaluator(this->expression,
            environment,
            dynamic_pointer_cast<Node>(this->shared_from_this()),
            dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()),
            evaluation_config,
            "");

  set<ReevaluationEntry,
      ReevaluationOrderComparer> reevaluation_queue;
  stack< shared_ptr<Node> > touched_nodes;
  vector< shared_ptr<Node> > touched_nodes2;
  ProposalInfo this_proposal; // FIXME: define?
  stack<OmitPattern> omit_patterns;
  shared_ptr<ReevaluationParameters> reevaluation_parameters =
    shared_ptr<ReevaluationParameters>(
      new ReevaluationParameters(
        shared_ptr<NodeXRPApplication>(),
        reevaluation_queue,
        touched_nodes,
        touched_nodes2,
        this_proposal,
        omit_patterns));
  reevaluation_parameters->we_are_in_enumeration = false;

  ConstrainingResult constraining_result =
    ConstrainBranch(this->expression, this->observed_value, reevaluation_parameters, 1);
            
  if (constraining_result == CONSTRAININGRESULT_CANNOT_CONSTRAIN) {
    // Doing nothing, because we have marked the flag "__unsatisfied_constraint" in the function "ConstrainBranch".
    evaluation_config.unsatisfied_constraint = true;
  } else if (constraining_result == CONSTRAININGRESULT_ALREADY_PROPER_VALUE) {
    // Doing nothing.
    // Though, we should finalize below, otherwise maybe we do not deleted the node from the random choices pool.
  } else if (constraining_result == CONSTRAININGRESULT_VALUE_HAS_BEEN_CHANGED) {
    PropagateNewValue(reevaluation_queue, touched_nodes, touched_nodes2, this_proposal, reevaluation_parameters);
  } else {
    throw std::runtime_error("Strange 'constraining_result'.");
  }
  
  FinalizeProposal(MH_APPROVED, reevaluation_parameters);
  
  return NIL_INSTANCE;
}

shared_ptr<VentureValue>
NodeSelfEvaluating::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  return this->value;
}

shared_ptr<VentureValue>
NodeLambdaCreator::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  this->returned_value = shared_ptr<VentureValue>(new VentureLambda(this->arguments, this->expressions, environment));
  return this->returned_value;
}

shared_ptr<VentureValue>
NodeLookup::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  return LookupValue(environment, this->symbol, dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()), false);
}

shared_ptr<VentureValue>
EvaluateApplication(shared_ptr<VentureValue> evaluated_operator,
                    shared_ptr<NodeEnvironment> local_environment,
                    size_t number_of_operands,
                    shared_ptr<NodeEvaluation>& application_node, // "By reference" is because we also set it in the application caller node.
                    shared_ptr<NodeApplicationCaller> application_caller_ptr,
                    EvaluationConfig& evaluation_config) {
  if (evaluated_operator->GetType() == LAMBDA) {
    shared_ptr<VentureList> enumerate_arguments = ToVentureType<VentureLambda>(evaluated_operator)->formal_arguments;
    size_t index = 0;
    while (enumerate_arguments->GetType() != NIL) {
      if (index >= number_of_operands) {
        throw std::runtime_error("Too few arguments have been passed to lambda.");
      }
      BindVariableToEnvironment(local_environment,
                                ToVentureType<VentureSymbol>(enumerate_arguments->car),
                                local_environment->local_variables[index]);
      index++;
      enumerate_arguments = GetNext(enumerate_arguments);
    }
    if (index != number_of_operands) {
      throw std::runtime_error("Too many arguments have been passed to lambda.");
    }
    
    application_node =
      shared_ptr<NodeEvaluation>(ToVentureType<VentureLambda>(evaluated_operator)->expressions.lock()->clone());
    // cout << "***" << ToVentureType<VentureLambda>(evaluated_operator)->expressions->GetUniqueID();
    // cout << " " << application_node->GetUniqueID() << endl;

    return Evaluator(application_node,
                     local_environment,
                     dynamic_pointer_cast<Node>(application_caller_ptr),
                     dynamic_pointer_cast<NodeEvaluation>(application_caller_ptr),
                     evaluation_config,
                     "");
  } else if (evaluated_operator->GetType() == XRP_REFERENCE) {
    // Just for mem now.
    // Maybe, implement it in the future in a better way.
    for (size_t index = 0; index < number_of_operands; index++) {
      BindVariableToEnvironment(local_environment,
                                shared_ptr<VentureSymbol>(new VentureSymbol("XRP_ARGUMENT_" + boost::lexical_cast<string>(index))),
                                local_environment->local_variables[index]);
    }

    application_node = shared_ptr<NodeEvaluation>(new NodeXRPApplication(
      dynamic_pointer_cast<VentureXRP>(evaluated_operator))); // Do not use ToVentureType(...)
                                                              // because we have checked
                                                              // the type in the IF condition.
    dynamic_pointer_cast<NodeXRPApplication>(application_node)->weak_ptr_to_me = dynamic_pointer_cast<NodeXRPApplication>(application_node->shared_from_this());
    
    return Evaluator(application_node,
                     local_environment,
                     dynamic_pointer_cast<Node>(application_caller_ptr),
                     dynamic_pointer_cast<NodeEvaluation>(application_caller_ptr),
                     evaluation_config,
                     "");
  } else {
    throw std::runtime_error((string("Attempt to apply neither LAMBDA nor XRP (") + boost::lexical_cast<string>(evaluated_operator->GetType()) + string(")")).c_str());
  }
}

shared_ptr<VentureValue>
NodeApplicationCaller::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  shared_ptr<VentureValue> evaluated_operator = Evaluator(application_operator,
                                                          environment,
                                                          dynamic_pointer_cast<Node>(this->shared_from_this()),
                                                          dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()),
                                                          evaluation_config,
                                                          "");
  assert(evaluated_operator != shared_ptr<VentureValue>());
  this->saved_evaluated_operator = evaluated_operator;
  
  shared_ptr<NodeEnvironment> previous_environment;
  if (evaluated_operator->GetType() == LAMBDA) {
    previous_environment = ToVentureType<VentureLambda>(evaluated_operator)->scope_environment.lock();
  } else {
    previous_environment = environment;
  }

  shared_ptr<NodeEnvironment> local_environment =
    shared_ptr<NodeEnvironment>(new NodeEnvironment(previous_environment));
  for (size_t index = 0; index < application_operands.size(); index++) {
    shared_ptr<VentureValue> binding_value =
      Evaluator(application_operands[index],
                environment,
                shared_ptr<Node>(),
                dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()),
                evaluation_config,
                "args_" + boost::lexical_cast<string>(index));
    shared_ptr<NodeVariable> new_variable_node =
      shared_ptr<NodeVariable>(new NodeVariable(local_environment, binding_value, application_operands[index]));
    new_variable_node->weak_ptr_to_me = dynamic_pointer_cast<NodeVariable>(new_variable_node->shared_from_this()); // Silly.
    local_environment->local_variables.push_back(new_variable_node);
    application_operands[index]->output_references.insert(new_variable_node);
  }
  
  return
    EvaluateApplication(evaluated_operator,
                        local_environment,
                        application_operands.size(),
                        application_node,
                        dynamic_pointer_cast<NodeApplicationCaller>(this->shared_from_this()),
                        evaluation_config);
}

vector< shared_ptr<VentureValue> >
GetArgumentsFromEnvironment(shared_ptr<NodeEnvironment> environment,
                            shared_ptr<NodeEvaluation> caller,
                            bool old_values = false) {
  if (old_values == true &&
      caller != shared_ptr<NodeEvaluation>() &&
      caller->GetNodeType() == XRP_APPLICATION &&
      dynamic_pointer_cast<NodeApplicationCaller>(caller->parent.lock())->new_application_node == caller) {
    assert(environment == caller->environment);
    environment = dynamic_pointer_cast<NodeApplicationCaller>(caller->parent.lock())->application_node->environment;
    // Not to add output references:
    caller = shared_ptr<NodeEvaluation>();
  }
  vector< shared_ptr<VentureValue> > arguments;
  for (size_t index = 0; index < environment->local_variables.size(); index++) {
    arguments.push_back(LookupValue(environment,
                                    index,
                                    caller,
                                    old_values));
  }
  return arguments;
}

shared_ptr<VentureValue>
NodeXRPApplication::Evaluate(shared_ptr<NodeEnvironment> environment, EvaluationConfig& evaluation_config) {
  //cout << "SIZE: " << GetArgumentsFromEnvironment(environment,
  //                                dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this())).size() << endl;
  vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(environment, // Not efficient?
                                  dynamic_pointer_cast<NodeEvaluation>(this->shared_from_this()));
  shared_ptr<VentureValue> new_sample =
    this->xrp->xrp->Sample(got_arguments,
                           dynamic_pointer_cast<NodeXRPApplication>(this->shared_from_this()),
                           evaluation_config);
  this->my_sampled_value = new_sample;
  return new_sample;
}

shared_ptr<ReevaluationResult> // FIXME: Why we pass ReevaluationResult as shared_ptr?
                               //        It is not enough to pass it as just value?
NodeXRPApplication::Reevaluate(shared_ptr<VentureValue> passing_value,
                               shared_ptr<Node> sender,
                               shared_ptr<ReevaluationParameters> reevaluation_parameters) { // Not efficient?
  return shared_ptr<ReevaluationResult>(
    new ReevaluationResult(shared_ptr<VentureValue>(), true));
}

shared_ptr<ReevaluationResult>
NodeEvaluation::Reevaluate(shared_ptr<VentureValue> passing_value,
                           shared_ptr<Node> sender,
                           shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  throw std::runtime_error(("This node does not have the Reevaluation function (node type " + boost::lexical_cast<string>(this->GetNodeType()) + ").").c_str());
}

shared_ptr<ReevaluationResult>
Node::Reevaluate(shared_ptr<VentureValue> passing_value,
                 shared_ptr<Node> sender,
                 shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  throw std::runtime_error(("This node does not have the Reevaluation function (node type " + boost::lexical_cast<string>(this->GetNodeType()) + ").").c_str());
}

shared_ptr<ReevaluationResult>
NodeVariable::Reevaluate(shared_ptr<VentureValue> passing_value,
                 shared_ptr<Node> sender,
                 shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  assert(passing_value != shared_ptr<VentureValue>());
  this->new_value = passing_value;
  return shared_ptr<ReevaluationResult>( // FIXME: Not it does not change anything.
    new ReevaluationResult(passing_value, true));
}

shared_ptr<ReevaluationResult>
NodeLookup::Reevaluate(shared_ptr<VentureValue> passing_value,
                       shared_ptr<Node> sender,
                       shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  // Just passing up:
  return shared_ptr<ReevaluationResult>(
    new ReevaluationResult(passing_value, true));
}

void CopyLocalEnvironmentByContent
  (shared_ptr<NodeEnvironment> existing_environment,
   shared_ptr<NodeEnvironment> new_environment,
   vector< shared_ptr<NodeEvaluation> > binding_nodes)
{
  for (size_t index = 0; index < binding_nodes.size(); index++) {
    shared_ptr<VentureValue> binding_value =
      existing_environment->local_variables[index]->GetCurrentValue();
    weak_ptr<NodeEvaluation> binding_node =
      existing_environment->local_variables[index]->binding_node;
    shared_ptr<NodeVariable> new_variable_node =
      shared_ptr<NodeVariable>(new NodeVariable(new_environment, binding_value, binding_node));
    new_variable_node->weak_ptr_to_me = dynamic_pointer_cast<NodeVariable>(new_variable_node->shared_from_this()); // Silly.
    new_environment->local_variables.push_back(new_variable_node);
    binding_nodes[index]->output_references.insert(new_variable_node);
  }
}

shared_ptr<ReevaluationResult>
NodeApplicationCaller::Reevaluate__TryToRescore(shared_ptr<VentureValue> passing_value,
                                                shared_ptr<Node> sender,
                                                shared_ptr<ReevaluationParameters> reevaluation_parameters,
                                                shared_ptr<VentureXRP> xrp_reference) {
  shared_ptr<NodeEnvironment> local_environment = shared_ptr<NodeEnvironment>(new NodeEnvironment(this->application_node->environment->parent_environment.lock()));
  CopyLocalEnvironmentByContent(this->application_node->environment, local_environment, application_operands);
    
  assert(this->new_application_node == shared_ptr<NodeXRPApplication>());
  this->new_application_node =
    shared_ptr<NodeXRPApplication>(
      new NodeXRPApplication(*dynamic_pointer_cast<NodeXRPApplication>(this->application_node)));
  dynamic_pointer_cast<NodeXRPApplication>(new_application_node)->weak_ptr_to_me = dynamic_pointer_cast<NodeXRPApplication>(new_application_node->shared_from_this());
  assert(dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->GetNodeType() == dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->GetNodeType());
  assert(dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->output_references.size() == dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->output_references.size());
  assert(dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->shared_from_this() != dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->shared_from_this());
  dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->xrp = xrp_reference;
  dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->environment = local_environment;
  dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->constraint_times = 0; // Because it would be constraint soon by separate operation.
  dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->already_absorbed = -1;
  
  if (passing_value != shared_ptr<VentureValue>()) {
    dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->my_sampled_value = passing_value;
  }

  vector< shared_ptr<VentureValue> > got_old_arguments = GetArgumentsFromEnvironment(this->application_node->environment,
    dynamic_pointer_cast<NodeEvaluation>(this->application_node), true);

  // Should be with adding references!
  vector< shared_ptr<VentureValue> > got_new_arguments = GetArgumentsFromEnvironment(local_environment,
    dynamic_pointer_cast<NodeEvaluation>(this->new_application_node), false);
    
  EvaluationConfig tmp_evaluation_config(true, reevaluation_parameters->shared_from_this());
    
  bool value_has_changed = true;
  if (passing_value != shared_ptr<VentureValue>() &&
        CompareValue(passing_value, dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->my_sampled_value)) {
    value_has_changed = false;
  }

  shared_ptr<RescorerResamplerResult> result =
    xrp_reference->xrp->RescorerResampler(
      got_old_arguments,
      got_new_arguments,
      dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node),
      (sender == reevaluation_parameters->principal_node),
      reevaluation_parameters,
      tmp_evaluation_config,
      value_has_changed);

  if (result->new_value != shared_ptr<VentureValue>()) { // Resampled.
    this->MH_made_action = MH_ACTION__RESAMPLED;
    reevaluation_parameters->__log_p_new += tmp_evaluation_config.__log_unconstrained_score;
    reevaluation_parameters->__log_q_from_old_to_new += tmp_evaluation_config.__log_unconstrained_score;
    assert(result->new_loglikelihood == log(1.0) || xrp_reference->xrp->IsRandomChoice() == true); // For now all XRPs, which are being resampled and which are not forced to be resampled, should return it.
    dynamic_pointer_cast<NodeXRPApplication>(this->new_application_node)->my_sampled_value = result->new_value;
    return shared_ptr<ReevaluationResult>(
      new ReevaluationResult(result->new_value, true));
  } else { // Rescored.
    reevaluation_parameters->__log_p_new += tmp_evaluation_config.__log_unconstrained_score;
    this->MH_made_action = MH_ACTION__RESCORED;
    return shared_ptr<ReevaluationResult>(
      new ReevaluationResult(shared_ptr<VentureValue>(), false));
  }
}

#include <math.h>
double lgamma(double x)
{
    double x0,x2,xp,gl,gl0;
    int n,k;
    static double a[] = {
        8.333333333333333e-02,
       -2.777777777777778e-03,
        7.936507936507937e-04,
       -5.952380952380952e-04,
        8.417508417508418e-04,
       -1.917526917526918e-03,
        6.410256410256410e-03,
       -2.955065359477124e-02,
        1.796443723688307e-01,
       -1.39243221690590};
    
    x0 = x;
    if (x <= 0.0) return 1e308;
    else if ((x == 1.0) || (x == 2.0)) return 0.0;
    else if (x <= 7.0) {
        n = (int)(7-x);
        x0 = x+n;
    }
    x2 = 1.0/(x0*x0);
    xp = 2.0*3.14159265358979323846264338327950;
    gl0 = a[9];
    for (k=8;k>=0;k--) {
        gl0 = gl0*x2 + a[k];
    }
    gl = gl0/x0+0.5*log(xp)+(x0-0.5)*log(x0)-x0;
    if (x <= 7.0) {
        for (k=1;k<=n;k++) {
            gl -= log(x0-1.0);
            x0 -= 1.0;
        }
    }
    return gl;
}

shared_ptr<ReevaluationResult>
NodeApplicationCaller::Reevaluate(shared_ptr<VentureValue> passing_value,
                                  shared_ptr<Node> sender,
                                  shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  assert(this->MH_made_action == MH_ACTION__EMPTY_STATUS);
  
  if (sender == this->application_node->shared_from_this() &&
        this->application_node->GetNodeType() == XRP_APPLICATION &&
        passing_value == shared_ptr<VentureValue>())
  {

  } else if (sender == this->application_node->shared_from_this()) {
      // Just passing up (came from lambda or from memoized procedure).
      this->MH_made_action = MH_ACTION__LAMBDA_PROPAGATED;
      return shared_ptr<ReevaluationResult>(
        new ReevaluationResult(passing_value, true));
  }


  if (sender == this->application_node->shared_from_this() &&
        this->application_node->GetNodeType() == XRP_APPLICATION &&
        passing_value == shared_ptr<VentureValue>())
  {
    if (sender != reevaluation_parameters->principal_node) {
      if (dynamic_pointer_cast<NodeXRPApplication>(sender)->xrp->xrp->GetName() == "XRP__SymmetricDirichletMultinomial_maker" &&
            global_environment->variables.count("fast-calc-joint-prob") == 1) {
        vector< shared_ptr<VentureValue> > got_old_arguments = GetArgumentsFromEnvironment(this->application_node->environment,
          dynamic_pointer_cast<NodeEvaluation>(this->application_node), true);

        // Should be with adding references!
        vector< shared_ptr<VentureValue> > got_new_arguments = GetArgumentsFromEnvironment(this->application_node->environment,
          dynamic_pointer_cast<NodeEvaluation>(this->application_node), false);

        shared_ptr<XRP__DirichletMultinomial_sampler> xrpobject =
          dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(dynamic_pointer_cast<VentureXRP>(dynamic_pointer_cast<NodeXRPApplication>(sender)->my_sampled_value)->xrp);
        
        assert(got_old_arguments[1]->GetInteger() == got_new_arguments[1]->GetInteger());

        double old_a = got_old_arguments[0]->GetReal();
        double new_a = got_new_arguments[0]->GetReal();

        double old_A = old_a * got_old_arguments[1]->GetInteger();
        double new_A = new_a * got_new_arguments[1]->GetInteger();

        // vector<double> Ns(got_old_arguments[1]->GetInteger());
        double N = 0.0;

        for (size_t index = 0; index < got_old_arguments[1]->GetInteger(); index++) {
          //Ns[index] = xrpobject->statistics[index] - old_a;
          N += xrpobject->statistics[index] - old_a;
        }

        double oldlogP = lgamma(old_A) - lgamma(old_A + N);
        double newlogP = lgamma(new_A) - lgamma(new_A + N);

        for (size_t index = 0; index < got_old_arguments[1]->GetInteger(); index++) {
          oldlogP += lgamma(xrpobject->statistics[index]);
          newlogP += lgamma(xrpobject->statistics[index] + new_a - old_a);

          xrpobject->statistics[index] += new_a - old_a;
        }
        
        oldlogP -= lgamma(old_a) * got_old_arguments[1]->GetInteger();
        newlogP -= lgamma(new_a) * got_old_arguments[1]->GetInteger();

        xrpobject->sum_of_statistics += (new_a - old_a) * got_old_arguments[1]->GetInteger();
        xrpobject->old_a = old_a;
        xrpobject->new_a = new_a;

        reevaluation_parameters->__log_p_old += oldlogP;
        reevaluation_parameters->__log_p_new += newlogP;

        this->MH_made_action = MH_ACTION__SDD_RESCORED;
        return shared_ptr<ReevaluationResult>(
          new ReevaluationResult(shared_ptr<VentureValue>(), false));
      }

      if (dynamic_pointer_cast<NodeXRPApplication>(sender)->xrp->xrp->GetName() == "XRP__CRPmaker" &&
            global_environment->variables.count("fast-calc-joint-prob") == 1) {
        vector< shared_ptr<VentureValue> > got_old_arguments = GetArgumentsFromEnvironment(this->application_node->environment,
          dynamic_pointer_cast<NodeEvaluation>(this->application_node), true);

        // Should be with adding references!
        vector< shared_ptr<VentureValue> > got_new_arguments = GetArgumentsFromEnvironment(this->application_node->environment,
          dynamic_pointer_cast<NodeEvaluation>(this->application_node), false);

        shared_ptr<XRP__CRPsampler> xrpobject =
          dynamic_pointer_cast<XRP__CRPsampler>(dynamic_pointer_cast<VentureXRP>(dynamic_pointer_cast<NodeXRPApplication>(sender)->my_sampled_value)->xrp);
        
        // In the Wikipedia article:
        // --- their theta is our alpha
        // --- their alpha is equal to 0
        // --- |B| is number of tables
        // --- n is number of customers
        real number_of_tables = xrpobject->atoms.size();
        real number_of_customers = xrpobject->current_number_of_clients;
        
        reevaluation_parameters->__log_p_old += lgamma(got_old_arguments[0]->GetReal()) + number_of_tables * log(got_old_arguments[0]->GetReal()) - lgamma(got_old_arguments[0]->GetReal() + number_of_customers);
        reevaluation_parameters->__log_p_new += lgamma(got_new_arguments[0]->GetReal()) + number_of_tables * log(got_new_arguments[0]->GetReal()) - lgamma(got_new_arguments[0]->GetReal() + number_of_customers);

        xrpobject->old_alpha = xrpobject->alpha;
        xrpobject->alpha = got_new_arguments[0]->GetReal();

        this->MH_made_action = MH_ACTION__SDD_RESCORED;
        return shared_ptr<ReevaluationResult>(
          new ReevaluationResult(shared_ptr<VentureValue>(), false));
      }
    }
  }

  shared_ptr<ReevaluationResult> reevaluation_result;
  
  reevaluation_parameters->__tmp_for_unconstrain = 0.0;
  shared_ptr<VentureValue> value_for_constraining;
  if (this->constraint_times > 0) {
    value_for_constraining = UnconstrainBranch(this->application_node, this->constraint_times, reevaluation_parameters);
    //cout << "Unconstraining value: " << value_for_constraining->GetString() << endl;
  }

  if (this->already_absorbed == MHid) {
    throw std::runtime_error("The node, which is calling the AbsorbBranchProbability, already was absorbed by somebody!");
  }
  //cout << "Absorb call from. ";
  //PrintVector(this->myorder);
  pair<real, real> branch_loglikelihoods = AbsorbBranchProbability(this->application_node, reevaluation_parameters);
  
  reevaluation_parameters->__log_p_old += branch_loglikelihoods.first; // logP_constraint
  reevaluation_parameters->__log_p_old += branch_loglikelihoods.second; // logP_unconstraint

  if (sender == this->application_node->shared_from_this() &&
        this->application_node->GetNodeType() == XRP_APPLICATION &&
        passing_value == shared_ptr<VentureValue>())
  {
    // Either:
    // 1) it is a principal node,
    // 2) arguments have changed.
    reevaluation_result = this->Reevaluate__TryToRescore(passing_value, sender, reevaluation_parameters, dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->xrp);
    
    if (this->MH_made_action == MH_ACTION__RESAMPLED) { // This construction repeats three times.
      reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
      reevaluation_parameters->__log_q_from_new_to_old += reevaluation_parameters->__tmp_for_unconstrain;
    } else if (this->MH_made_action == MH_ACTION__RESCORED) {
      // reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
    }
  } else if (sender == this->application_operator->shared_from_this()) {
    // Operator has changed.
    
    assert(passing_value != shared_ptr<VentureValue>());
    this->proposing_evaluated_operator = passing_value;
    shared_ptr<VentureValue> evaluated_operator = passing_value;

    if (this->application_node->GetNodeType() == XRP_APPLICATION &&
          evaluated_operator->GetType() == XRP_REFERENCE &&
          dynamic_pointer_cast<VentureXRP>(evaluated_operator)->xrp->GetName() ==
            dynamic_pointer_cast<NodeXRPApplication>(this->application_node)->xrp->xrp->GetName() &&
          dynamic_pointer_cast<VentureXRP>(evaluated_operator)->xrp->CouldBeRescored())
    {
      reevaluation_result = this->Reevaluate__TryToRescore(shared_ptr<VentureValue>(), sender, reevaluation_parameters, dynamic_pointer_cast<VentureXRP>(evaluated_operator));

      if (this->MH_made_action == MH_ACTION__RESAMPLED) { // This construction repeats three times.
        reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
        reevaluation_parameters->__log_q_from_new_to_old += reevaluation_parameters->__tmp_for_unconstrain;
      } else if (this->MH_made_action == MH_ACTION__RESCORED) {
        // reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
      }
    } else {
      this->MH_made_action = MH_ACTION__RESAMPLED;

      if (this->MH_made_action == MH_ACTION__RESAMPLED) { // This construction repeats three times.
        reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
        reevaluation_parameters->__log_q_from_new_to_old += reevaluation_parameters->__tmp_for_unconstrain;
      } else if (this->MH_made_action == MH_ACTION__RESCORED) {
        // reevaluation_parameters->__log_q_from_new_to_old += branch_loglikelihoods.second; // logP_unconstraint
      }
      
      shared_ptr<NodeEnvironment> previous_environment; // This part should be in the "EvaluateApplication(...)"
                                                        // in order to avoid duplication.
      if (evaluated_operator->GetType() == LAMBDA) {
        previous_environment = ToVentureType<VentureLambda>(evaluated_operator)->scope_environment.lock();
      } else {
        previous_environment = environment;
      }

      shared_ptr<NodeEnvironment> local_environment =
        shared_ptr<NodeEnvironment>(new NodeEnvironment(previous_environment));
      CopyLocalEnvironmentByContent(this->application_node->environment, local_environment, application_operands);

      EvaluationConfig local_evaluation_config(true, reevaluation_parameters->shared_from_this());

      shared_ptr<VentureValue> new_value =
        EvaluateApplication(passing_value,
                            local_environment,
                            application_operands.size(),
                            new_application_node,
                            dynamic_pointer_cast<NodeApplicationCaller>(this->shared_from_this()),
                            local_evaluation_config);
      reevaluation_parameters->__log_p_new += local_evaluation_config.__log_unconstrained_score;
      // Commented, because during evaluation we cannot have constrained scores
      // reevaluation_parameters->__log_p_new += local_evaluation_config.__log_constrained_score;
      reevaluation_parameters->__log_q_from_old_to_new += local_evaluation_config.__log_unconstrained_score;

      reevaluation_result = shared_ptr<ReevaluationResult>(
        new ReevaluationResult(new_value, true));
    }
  } else {
    throw std::runtime_error("NodeApplicationCaller::Reevaluate: strange sender.");
  }

  if (this->constraint_times > 0) {
    ConstrainingResult constraining_result =
      ConstrainBranch(this->new_application_node, value_for_constraining, reevaluation_parameters, this->constraint_times);
    //cout << "Constraining result: " << constraining_result << endl;
    //if (reevaluation_result->passing_value != shared_ptr<VentureValue>()) {
    //  cout << "Passing value: " << reevaluation_result->passing_value->GetString() << endl;
    //}
    //cout << "Pass further?: " << reevaluation_result->pass_further << endl;
      
    if (constraining_result == CONSTRAININGRESULT_CANNOT_CONSTRAIN) {
      // Doing nothing, because we have marked the flag "__unsatisfied_constraint" in the function "ConstrainBranch".
      return shared_ptr<ReevaluationResult>(
        new ReevaluationResult(shared_ptr<VentureValue>(), false));
    } else if (constraining_result == CONSTRAININGRESULT_ALREADY_PROPER_VALUE) {
      assert(reevaluation_result->pass_further == false || CompareValue(reevaluation_result->passing_value, value_for_constraining));
      return reevaluation_result;
    } else if (constraining_result == CONSTRAININGRESULT_VALUE_HAS_BEEN_CHANGED) {
      // We have added propagation in the function "ConstrainBranch".
      assert(this->already_propagated == shared_ptr<VentureValue>());
      this->already_propagated = value_for_constraining;
      return shared_ptr<ReevaluationResult>(
        new ReevaluationResult(value_for_constraining, true));
    } else {
      throw std::runtime_error("Strange 'constraining_result'.");
    }
  } else {
    return reevaluation_result;
  }
}

shared_ptr<ReevaluationResult>
NodeDirectiveAssume::Reevaluate(shared_ptr<VentureValue> passing_value,
                                shared_ptr<Node> sender,
                                shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  this->my_new_value = passing_value;
  // Just passing up:
  return shared_ptr<ReevaluationResult>(
    new ReevaluationResult(passing_value, true));
}

shared_ptr<ReevaluationResult>
NodeDirectivePredict::Reevaluate(shared_ptr<VentureValue> passing_value,
                                 shared_ptr<Node> sender,
                                 shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  this->my_new_value = passing_value;
  // Just passing up:
  return shared_ptr<ReevaluationResult>(
    new ReevaluationResult(passing_value, true));
}

shared_ptr<ReevaluationResult>
NodeDirectiveObserve::Reevaluate(shared_ptr<VentureValue> passing_value,
                                 shared_ptr<Node> sender,
                                 shared_ptr<ReevaluationParameters> reevaluation_parameters) {
  if (CompareValue(passing_value, this->observed_value)) {
    return shared_ptr<ReevaluationResult>(
      new ReevaluationResult(shared_ptr<VentureValue>(), false));
  } else {
    cout << passing_value->GetString() << endl;
    cout << this->observed_value->GetString() << endl;
    cout << reevaluation_parameters->__unsatisfied_constraint << endl;
    DrawGraphDuringMH(reevaluation_parameters->touched_nodes);
    throw std::runtime_error("The OBSERVE directive's node should not be reevaluated with passing value != observed_value.");
  }

  /*
  pair<bool, shared_ptr<NodeEvaluation> > forcing_result = ForceExpressionValue(this->expression, this->observed_value, reevaluation_parameters);
  if (forcing_result.first == false) {
    reevaluation_parameters->__unsatisfied_constraint = true;
  }
  if (forcing_result.second == shared_ptr<NodeEvaluation>()) {
    return shared_ptr<ReevaluationResult>(
      new ReevaluationResult(shared_ptr<VentureValue>(), false));
  } else {
    return shared_ptr<ReevaluationResult>(
      new ReevaluationResult(forcing_result.second, true));
  }
  */
}

void ApplyToMeAndAllMyChildren(shared_ptr<Node> first_node,
                               bool old_values,
                               void (*f)(shared_ptr<Node>, bool)) {
  queue< shared_ptr<Node> > processing_queue;
  processing_queue.push(first_node);
  while (!processing_queue.empty()) {
    if (processing_queue.front()->WasEvaluated() == false) {
      processing_queue.pop();
      continue;
      // We assume that not evaluated yet node just will be removed
      // when its parent will be removed, because there is no cycled
      // pointers.
    }
    if (processing_queue.front() != first_node &&
         (processing_queue.front()->GetNodeType() == DIRECTIVE_ASSUME || 
           processing_queue.front()->GetNodeType() == DIRECTIVE_PREDICT || 
           processing_queue.front()->GetNodeType() == DIRECTIVE_OBSERVE)) {
      // Do not delete children, which are directives itself.
      processing_queue.pop();
      continue;
    }
    processing_queue.front()->GetChildren(processing_queue);
    (*f)(dynamic_pointer_cast<NodeEvaluation>(processing_queue.front()->shared_from_this()), old_values);
    processing_queue.pop();
  }
}

bool Node::WasEvaluated() {
  return false;
}

bool NodeEvaluation::WasEvaluated() {
  return this->evaluated;
}

string NodeEvaluation::__GetLocationAsString() {
  string return_string;
  for (size_t index = 0; index < this->myorder.size(); index++) {
    if (index > 0) {
      return_string += ":";
    }
    return_string += boost::lexical_cast<string>(myorder[index]);
  }
  return return_string;
}

void DrawGraphDuringMH(stack< shared_ptr<Node> >& touched_nodes) {
#ifdef _MSC_VER
  cout << "Writing the graph" << endl;

  std::ofstream graph_file;
  graph_file.open("C:/Temp/graph_output.txt");
  graph_file << "digraph G {" << endl;
  
  queue< pair< string, shared_ptr<Node> > > processing_queue;

  map<size_t, directive_entry>::reverse_iterator previous = directives.rend();
  for (map<size_t, directive_entry>::reverse_iterator directive = directives.rbegin();
       directive != directives.rend();
       directive++) {
    if (previous == directives.rend()) {
      processing_queue.push(make_pair("", directive->second.directive_node));
    } else {
      processing_queue.push(make_pair(previous->second.directive_node->GetUniqueID(), directive->second.directive_node));
    }
    previous = directive;
  }

  stack< shared_ptr<Node> > touched_nodes3 = touched_nodes;
  while (!touched_nodes3.empty()) {
    shared_ptr<Node> node = touched_nodes3.top();
    while (dynamic_pointer_cast<NodeEvaluation>(node) != shared_ptr<NodeEvaluation>())
    {
      dynamic_pointer_cast<NodeEvaluation>(node)->_marked = true;
      node = dynamic_pointer_cast<NodeEvaluation>(node)->parent.lock();
    }
    touched_nodes3.pop();
  }

  while (!processing_queue.empty()) {
    queue< shared_ptr<Node> > temporal_queue;
    if (processing_queue.front().second == shared_ptr<Node>()) {
      processing_queue.pop();
      continue; // It means that some not yet evaluated node returned its not ready child
                // (i.e. not existing yet child).
    }
    processing_queue.front().second->GetChildren(temporal_queue);
    shared_ptr<Node> current_node = processing_queue.front().second; // FIXME: to delete.
    if (processing_queue.front().second->GetNodeType() == APPLICATION_CALLER) {
      if (dynamic_pointer_cast<NodeApplicationCaller>(processing_queue.front().second)->new_application_node != shared_ptr<NodeEvaluation>()) {
        temporal_queue.push(dynamic_pointer_cast<NodeApplicationCaller>(processing_queue.front().second)->new_application_node);
        touched_nodes.push(dynamic_pointer_cast<NodeApplicationCaller>(processing_queue.front().second)->new_application_node);
      }
    }
    if (processing_queue.front().second->GetNodeType() == XRP_APPLICATION &&
          dynamic_pointer_cast<NodeXRPApplication>(processing_queue.front().second)->xrp->xrp->GetName() == "XRP__memoizer")
    {
      // FIXME: XRP__memoizer_map_element should be renamed to XRP__memoized_procedure_map_element.
      for (map<string, XRP__memoizer_map_element>::iterator iterator = dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<VentureXRP>(dynamic_pointer_cast<NodeXRPApplication>(processing_queue.front().second)->my_sampled_value)->xrp)->mem_table.begin();
           iterator != dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<VentureXRP>(dynamic_pointer_cast<NodeXRPApplication>(processing_queue.front().second)->my_sampled_value)->xrp)->mem_table.end();
           iterator++)
      {
        temporal_queue.push(iterator->second.application_caller_node);
        touched_nodes.push(iterator->second.application_caller_node);
      }
    }
    while (!temporal_queue.empty()) {
      processing_queue.push(make_pair(processing_queue.front().second->GetUniqueID(), temporal_queue.front()));
      temporal_queue.pop();
    }
    std::deque< shared_ptr<Node> >::const_iterator already_existent_element =
      std::find(GetStackContainer(touched_nodes).begin(), GetStackContainer(touched_nodes).end(), processing_queue.front().second);
    if (!(std::find(GetStackContainer(touched_nodes).begin(), GetStackContainer(touched_nodes).end(), processing_queue.front().second) ==
          GetStackContainer(touched_nodes).end()) ||
        processing_queue.front().second->_marked == true)
    {
      graph_file << "  Node" << processing_queue.front().second->GetUniqueID() << " [label=\"";
      if (!(already_existent_element == GetStackContainer(touched_nodes).end())) {
        int distance = std::distance(GetStackContainer(touched_nodes).begin(), already_existent_element);
        graph_file << "[MH" << distance << "] ";
      }
      graph_file << "(" << processing_queue.front().second->WasEvaluated() << ") ";
      graph_file << processing_queue.front().second->GetUniqueID() << ". ";
      graph_file << GetNodeTypeAsString(processing_queue.front().second->GetNodeType())
        << ": " << processing_queue.front().second->GetContent();
      graph_file << "\\n" << processing_queue.front().second->comment;
      graph_file << "\\n" << dynamic_pointer_cast<NodeEvaluation>(processing_queue.front().second)->node_key;
      graph_file << "\\nCT: " << dynamic_pointer_cast<NodeEvaluation>(processing_queue.front().second)->constraint_times;
      graph_file << "\\nOrder: ";
      vector<size_t> order = dynamic_pointer_cast<NodeEvaluation>(processing_queue.front().second)->myorder;
      for (size_t index_m = 0; index_m < order.size(); index_m++) {
        graph_file << order[index_m] << " ";
      }
      graph_file << "\"" << endl;
      if (!(already_existent_element == GetStackContainer(touched_nodes).end())) {
        graph_file << ",color=red";
      }
      graph_file << "]";
      if (processing_queue.front().first != "") {
        graph_file << "  Node" << processing_queue.front().first << " -> "
          << "Node" << processing_queue.front().second->GetUniqueID() << endl;
      }
    }

    processing_queue.pop();
  }

  graph_file << "}" << endl;
  graph_file.close();

  cout << "The graph has been written" << endl;
#endif
}

void AddToRandomChoices(weak_ptr<NodeXRPApplication> random_choice) {
  assert(random_choice.lock()->GetType() == NODE && random_choice.lock()->GetNodeType() == XRP_APPLICATION);
  pair< set< weak_ptr<NodeXRPApplication> >::iterator, bool > result = random_choices.insert(random_choice);
  if (result.second == true) { // New element has been inserted.
    random_choices_vector.push_back(result.first);
    random_choice.lock()->location_in_random_choices = random_choices_vector.size() - 1; // FIXME: not multithread safe!
  }
}
void DeleteRandomChoices(weak_ptr<NodeXRPApplication> random_choice, size_t index) {
  set< weak_ptr<NodeXRPApplication> >::iterator random_choice_iterator = random_choices.find(random_choice);
  if (random_choice_iterator != random_choices.end()) {
    // FIXME: not multithread safe!
    if (random_choice.lock()) {
      random_choices_vector.back()->lock()->location_in_random_choices = random_choice.lock()->location_in_random_choices;
      random_choices_vector[random_choice.lock()->location_in_random_choices] = random_choices_vector.back();
    } else {
      // Assuming that index is provided.
      if (index + 1 != random_choices_vector.size()) {
        random_choices_vector.back()->lock()->location_in_random_choices = index;
        random_choices_vector[index] = random_choices_vector.back();
      }
    }
    random_choices_vector.pop_back();
    random_choices.erase(random_choice_iterator);
  }
}
size_t GetSizeOfRandomChoices() {
  return random_choices.size();
}
void ClearRandomChoices() {
  random_choices.clear();
  random_choices_vector.clear();
}
shared_ptr<NodeXRPApplication> GetRandomRandomChoice() {
//  set< weak_ptr<NodeXRPApplication> >::iterator iterator = random_choices.begin();
//  int random_choice_id = UniformDiscrete(0, GetSizeOfRandomChoices() - 1);
//  std::advance(iterator, random_choice_id);
//  return (*iterator).lock();
  int random_choice_id = UniformDiscrete(0, GetSizeOfRandomChoices() - 1);
  return random_choices_vector[random_choice_id]->lock();
}

NodeConstainingTemplate::NodeConstainingTemplate()
{
  
}

void PrintVector(vector<size_t> input) {
  cout << "Printing a vector:";
  for (size_t index = 0; index < input.size(); index++) {
    cout << " " << input[index];
  }
  cout << endl;
}
