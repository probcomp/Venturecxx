
#ifndef VENTURE___RIPL_H
#define VENTURE___RIPL_H

#include "Header.h"
#include "Analyzer.h"
#include "Evaluator.h"
#include "ERPs.h"
#include "XRPmem.h"
#include "XRPs.h"
#include "Primitives.h"
#include "MHProposal.h"

struct directive_entry {
  // Notice:
  // Could be implemented as "class",
  // i.e. has a constructor and a destructor,
  // and i.e. some issues below could be
  // done here (I mean deletion of all nodes).
  directive_entry(string directice_as_string,
                  shared_ptr<NodeEvaluation> directive_node);
  directive_entry();

  string directice_as_string;
  shared_ptr<NodeEvaluation> directive_node;
};
extern shared_ptr<NodeEnvironment> global_environment;
extern size_t last_directive_id;
extern map<size_t, directive_entry> directives;

shared_ptr<NodeEvaluation> GetLastDirectiveNode();

extern bool need_to_return_inference;
extern int continuous_inference_status;
void* ContinuousInference(void* arguments);
void PauseInference();
void ReturnInferenceIfNecessary();
void DeleteRIPL();
void ClearRIPL();
void InitRIPL();
shared_ptr<VentureValue> ReportValue(size_t directive_id);
void ForgetDirective(size_t directive_id);

struct directive_entry__only_expression {
  NodeTypes node_type;
  shared_ptr<VentureSymbol> name;
  shared_ptr<VentureValue> original_expression;
  shared_ptr<VentureValue> observed_value;
  string directive_as_string;
};

void RejectionSamplingForObserve();
bool ExecuteDirective(string& directive_as_string,
                        shared_ptr<NodeEvaluation> directive_node,
                        shared_ptr<VentureValue> original_expression);

size_t ExecuteDirectiveWithRejectionSampling
(string& directive_as_string,
 shared_ptr<NodeEvaluation> directive_node,
 shared_ptr<VentureValue> original_expression);

void BindStandardElementsToGlobalEnvironment();






real GetLogscoreOfDirective(shared_ptr<Node> first_node);

void RestoreDirective(shared_ptr<Node> first_node);

real GetLogscoreOfAllDirectives();

#endif
