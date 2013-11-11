
#ifndef VENTURE___ANALYZER_H
#define VENTURE___ANALYZER_H

#include "Header.h"
#include "VentureValues.h"
#include "XRPCore.h"

struct ReevaluationParameters;
extern shared_ptr<ReevaluationParameters> global_reevaluation_parameters;

enum NodeTypes { UNDEFINED_NODE, ENVIRONMENT, VARIABLE, UNDEFINED_EVALUATION_NODE, DIRECTIVE_ASSUME,
                 DIRECTIVE_PREDICT, DIRECTIVE_OBSERVE, SELF_EVALUATING, LAMBDA_CREATOR,
                 LOOKUP, APPLICATION_CALLER, XRP_APPLICATION};

enum MHMadeActions { MH_ACTION__EMPTY_STATUS, MH_ACTION__RESCORED, MH_ACTION__RESAMPLED, MH_ACTION__LAMBDA_PROPAGATED, MH_ACTION__SDD_RESCORED };

string GetNodeTypeAsString(size_t node_type);

extern size_t DIRECTIVE_COUNTER;

struct ProposalInfo;

struct NodeDirectiveObserve;
struct EvaluationConfig {
  EvaluationConfig(bool in_proposal, shared_ptr<ReevaluationParameters> reevaluation_config_ptr) : // Move to Analyzer.cpp?
    __log_unconstrained_score(0.0),
    unsatisfied_constraint(false),
    in_proposal(in_proposal),
    reevaluation_config_ptr(reevaluation_config_ptr)
  {}

  real __log_unconstrained_score;
  bool unsatisfied_constraint;
  bool in_proposal;
  
  shared_ptr<ReevaluationParameters> reevaluation_config_ptr;
};

struct Node : public VentureValue {
  Node();
  virtual VentureDataTypes GetType();
  virtual NodeTypes GetNodeType();
  virtual string GetUniqueID();
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>); // Should be in NodeEvaluation?
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  virtual bool WasEvaluated();
  virtual string GetContent();
  ~Node();

  virtual void DeleteNode();

  bool was_deleted;

  size_t constraint_times;
  
  string comment;

  shared_ptr<VentureValue> already_propagated;
  
  // boost::mutex occupying_mutex;
  shared_ptr<ProposalInfo> occupying_proposal_info;

  bool _marked;

  int already_absorbed;
};

struct NodeVariable;

struct NodeEnvironment : public Node {
  NodeEnvironment(shared_ptr<NodeEnvironment> parent_environment);
  virtual NodeTypes GetNodeType();
  ~NodeEnvironment();

  weak_ptr<NodeEnvironment> parent_environment;
  map<string, shared_ptr<NodeVariable> > variables;
  vector< shared_ptr<NodeVariable> > local_variables;
  
  virtual void DeleteNode();
};

struct NodeVariable : public Node {
  NodeVariable(shared_ptr<NodeEnvironment> parent_environment, shared_ptr<VentureValue> value, weak_ptr<NodeEvaluation> binding_node);
  virtual NodeTypes GetNodeType();
  shared_ptr<VentureValue> GetCurrentValue();
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                                  shared_ptr<Node>,
                                                                  shared_ptr<ReevaluationParameters>);
  ~NodeVariable();

  weak_ptr<NodeEnvironment> parent_environment;
  shared_ptr<VentureValue> value;
  shared_ptr<VentureValue> new_value;
  std::multiset< weak_ptr<Node> > output_references;
  weak_ptr<NodeEvaluation> binding_node;
  
  weak_ptr<Node> weak_ptr_to_me;
  
  virtual void DeleteNode();
};

struct NodeEvaluation : public Node {
  NodeEvaluation();
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<NodeEvaluation> clone() const;
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual bool WasEvaluated();
  ~NodeEvaluation();

  shared_ptr<NodeEnvironment> environment;
  weak_ptr<NodeEvaluation> parent;
  shared_ptr<NodeEvaluation> earlier_evaluation_nodes;
  bool evaluated;
  std::multiset< weak_ptr<Node> > output_references;
  vector<size_t> myorder;
  string __GetLocationAsString();
  size_t last_child_order;

  string node_key;
  
  virtual void DeleteNode();
};

const size_t REEVALUATION_PRIORITY__STANDARD = 10;
struct ReevaluationOrderComparer {
  bool operator()(const ReevaluationEntry& first, const ReevaluationEntry& second);
};

struct NodeDirectiveAssume : public NodeEvaluation {
  NodeDirectiveAssume(shared_ptr<VentureSymbol> name, shared_ptr<NodeEvaluation> expression);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  ~NodeDirectiveAssume();
  
  shared_ptr<VentureSymbol> name;
  shared_ptr<NodeEvaluation> expression;
  shared_ptr<VentureValue> my_value; // It should not be implemented in this way?
  shared_ptr<VentureValue> my_new_value; // It should not be implemented in this way?
  
  shared_ptr<VentureValue> original_expression;

  virtual void DeleteNode();
};

struct NodeDirectivePredict : public NodeEvaluation {
  NodeDirectivePredict(shared_ptr<NodeEvaluation> expression);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  ~NodeDirectivePredict();

  shared_ptr<NodeEvaluation> expression;
  shared_ptr<VentureValue> my_value; // It should not be implemented in this way?
  shared_ptr<VentureValue> my_new_value; // It should not be implemented in this way?
  
  shared_ptr<VentureValue> original_expression;

  virtual void DeleteNode();
};

struct NodeDirectiveObserve : public NodeEvaluation {
  NodeDirectiveObserve(shared_ptr<NodeEvaluation> expression, shared_ptr<VentureValue> observed_value);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  ~NodeDirectiveObserve();
  
  shared_ptr<NodeEvaluation> expression;
  shared_ptr<VentureValue> observed_value;
  
  shared_ptr<VentureValue> original_expression;

  virtual void DeleteNode();
};

struct NodeConstainingTemplate {
  NodeConstainingTemplate();
};

struct NodeSelfEvaluating : public NodeEvaluation, public NodeConstainingTemplate {
  NodeSelfEvaluating(shared_ptr<VentureValue> value);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<NodeEvaluation> clone() const;
  shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  // Using standard copy constructor.
  virtual string GetContent();
  ~NodeSelfEvaluating();
  
  shared_ptr<VentureValue> value;

  virtual void DeleteNode();
};

struct NodeLambdaCreator : public NodeEvaluation {
  NodeLambdaCreator(shared_ptr<VentureList> arguments, shared_ptr<NodeEvaluation> expressions);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<NodeEvaluation> clone() const;
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  // Using standard copy constructor.
  ~NodeLambdaCreator();
  
  shared_ptr<VentureList> arguments;
  shared_ptr<NodeEvaluation> expressions;
  shared_ptr<VentureValue> returned_value;

  virtual void DeleteNode();
};

struct NodeLookup : public NodeEvaluation {
  NodeLookup(shared_ptr<VentureSymbol> symbol);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<NodeEvaluation> clone() const;
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  virtual string GetContent();
  ~NodeLookup();

  shared_ptr<VentureSymbol> symbol;
  weak_ptr<NodeVariable> where_lookuped;

  weak_ptr<Node> weak_ptr_to_me;

  virtual void DeleteNode();
};

struct NodeApplicationCaller : public NodeEvaluation {
  NodeApplicationCaller(shared_ptr<NodeEvaluation> application_operator,
                        vector< shared_ptr<NodeEvaluation> >& application_operands);
  virtual NodeTypes GetNodeType();
  virtual shared_ptr<NodeEvaluation> clone() const;
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  shared_ptr<ReevaluationResult> Reevaluate__TryToRescore(shared_ptr<VentureValue> passing_value,
                                                          shared_ptr<Node> sender,
                                                          shared_ptr<ReevaluationParameters> reevaluation_parameters,
                                                          shared_ptr<VentureXRP> xrp_reference);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  ~NodeApplicationCaller();
  
  shared_ptr<VentureValue> saved_evaluated_operator;
  shared_ptr<VentureValue> proposing_evaluated_operator;
  shared_ptr<NodeEvaluation> application_operator;
  vector< shared_ptr<NodeEvaluation> > application_operands;
  shared_ptr<NodeEvaluation> application_node;
  shared_ptr<NodeEvaluation> new_application_node;

  MHMadeActions MH_made_action;
  
  virtual void DeleteNode();
};

struct NodeXRPApplication : public NodeEvaluation, public NodeConstainingTemplate {
  NodeXRPApplication(shared_ptr<VentureXRP> xrp);
  virtual NodeTypes GetNodeType();
  // It should not have clone() method?
  virtual shared_ptr<VentureValue> Evaluate(shared_ptr<NodeEnvironment>, EvaluationConfig& evaluation_config);
  virtual shared_ptr<ReevaluationResult> Reevaluate(shared_ptr<VentureValue>,
                                                    shared_ptr<Node>,
                                                    shared_ptr<ReevaluationParameters>);
  virtual void GetChildren(queue< shared_ptr<Node> >& processing_queue, size_t absorbing_parameter = 0);
  ~NodeXRPApplication();
  
  shared_ptr<VentureXRP> xrp;

  weak_ptr<NodeXRPApplication> weak_ptr_to_me; // FIXME: Should be weak_ptr<Node>.
  
  shared_ptr<VentureValue> my_sampled_value; // FIXME: Should be called "sampled_value".

  size_t location_in_random_choices;
  
  virtual void DeleteNode();
};

shared_ptr<NodeEvaluation> AnalyzeExpression(shared_ptr<VentureValue>);

vector< shared_ptr<VentureValue> >
GetArgumentsFromEnvironment(shared_ptr<NodeEnvironment>,
                            shared_ptr<NodeEvaluation>,
                            bool);

shared_ptr<VentureValue>
EvaluateApplication(shared_ptr<VentureValue> evaluated_operator,
                    shared_ptr<NodeEnvironment> local_environment,
                    size_t number_of_operands,
                    shared_ptr<NodeEvaluation>& application_node,
                    shared_ptr<NodeApplicationCaller> application_caller_ptr,
                    EvaluationConfig& evaluation_config);

void ApplyToMeAndAllMyChildren(shared_ptr<Node>,
                               bool old_values,
                               void (*f)(shared_ptr<Node>, bool));

void DrawGraphDuringMH(stack< shared_ptr<Node> >& touched_nodes);

void CopyLocalEnvironmentByContent
  (shared_ptr<NodeEnvironment> existing_environment,
   shared_ptr<NodeEnvironment> new_environment,
   vector< shared_ptr<NodeEvaluation> > binding_nodes);

void AddToRandomChoices(weak_ptr<NodeXRPApplication> random_choice);
void DeleteRandomChoices(weak_ptr<NodeXRPApplication> random_choice, size_t index = 0);
size_t GetSizeOfRandomChoices();
void ClearRandomChoices();
shared_ptr<NodeXRPApplication> GetRandomRandomChoice();

void PrintVector(vector<size_t> input);

#endif
