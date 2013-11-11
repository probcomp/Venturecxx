
#include "HeaderPre.h"
#include "Header.h"
#include "RIPL.h"

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
#include "ExternalXRPInterface.h"
#endif

#include "Shell_PPPs.h"

// Should be called DirectiveEntry!
directive_entry::directive_entry(string directice_as_string,
                shared_ptr<NodeEvaluation> directive_node)
  : directice_as_string(directice_as_string),
    directive_node(directive_node)
{}
directive_entry::directive_entry()
{
  throw std::runtime_error("Do not have default constructor.");
}

shared_ptr<NodeEvaluation> GetLastDirectiveNode() {
  if (directives.size() == 0) {
    throw std::runtime_error("There is no any directive in the trace.");
  }
  return directives.rbegin()->second.directive_node;
}

// http://cs.gmu.edu/~white/CS571/Examples/Pthread/create.c
void* ContinuousInference(void* arguments) {
  while (continuous_inference_status != 0) {
    //cout << " <I> ";
    if (continuous_inference_status == 1) {
      try {
        MakeMHProposal(shared_ptr<NodeXRPApplication>(),
                       shared_ptr<VentureValue>(),
                       shared_ptr< map<string, shared_ptr<VentureValue> > >(),
                       false);
      } catch (std::runtime_error& e) {
        continuous_inference_status = 0;
        cout << "Exception has been raised during continuous inference: " << e.what() << endl;
        return NULL;
      }
    } else if (continuous_inference_status == 2) {
      continuous_inference_status = 3;
      while (continuous_inference_status == 3) {
        //cout << "SleepingC" << endl;
        struct timespec ts = {0, 1}; // 1 ns -- is it okay? :)
#ifdef _MSC_VER
        pthread_delay_np(&ts);
#else
        nanosleep(&ts, NULL);
#endif
      }
    }
  }
  pthread_exit(0);
  return NULL;
}

void PauseInference() {
  if (continuous_inference_status == 1) {
    need_to_return_inference = true;
    continuous_inference_status = 2;
    clock_t start_time = clock();
    while (continuous_inference_status != 3) {
      if ((( static_cast<float>(clock() - start_time)) / CLOCKS_PER_SEC) > VENTURE__MAX_TIME_FOR_PAUSED_CONTINUOUS_INFERENCE) {
        throw std::runtime_error("Cannot stop the inference for more than " + boost::lexical_cast<string>(VENTURE__MAX_TIME_FOR_PAUSED_CONTINUOUS_INFERENCE) + " second(s).");
      }
      struct timespec ts = {0, 1}; // 1 ns -- is it okay? :)
#ifdef _MSC_VER
      pthread_delay_np(&ts);
#else
      nanosleep(&ts, NULL);
#endif
    }
  } else {
    need_to_return_inference = false;
  }
}

void ReturnInferenceIfNecessary() {
  if (need_to_return_inference == true) {
    continuous_inference_status = 1;
  }
}

void DeleteRIPL() {
  // Reconsider this function.
  
  //cout << "Size: " << directives.size() << endl;
  //cout << "Empty?: " << directives.empty() << endl;
  //cout << (directives.begin() == directives.end()) << endl;
  for (map<size_t, directive_entry>::iterator iterator = directives.begin(); iterator != directives.end(); iterator++) {
    DeleteBranch(iterator->second.directive_node, false);
  }

  global_environment = shared_ptr<NodeEnvironment>();

  directives.clear();
}

void ClearRIPL()
{
  DeleteRIPL();
  //assert(random_choices.size() == 0);
  ClearRandomChoices();
  if (continuous_inference_status != 0) {
    continuous_inference_status = 1;
  }
  InitRIPL();
}

void InitRIPL() {
  global_environment = shared_ptr<NodeEnvironment>(new NodeEnvironment(shared_ptr<NodeEnvironment>()));
  
  BindStandardElementsToGlobalEnvironment();

  last_directive_id = 0;
  DIRECTIVE_COUNTER = 0; // For "myorder".
  next_gensym_atom = 0;
}

shared_ptr<VentureValue> ReportValue(size_t directive_id) {
  if (directives.count(directive_id) == 0) {
    throw std::runtime_error("Attempt to report value for non-existent directive.");
  }
  if (directives[directive_id].directive_node->GetNodeType() == DIRECTIVE_ASSUME) {
    return dynamic_pointer_cast<NodeDirectiveAssume>(directives[directive_id].directive_node)->my_value;
  } else if (directives[directive_id].directive_node->GetNodeType() == DIRECTIVE_PREDICT) {
    return dynamic_pointer_cast<NodeDirectivePredict>(directives[directive_id].directive_node)->my_value;
  } else {
    throw std::runtime_error("Attempt to report value neither for ASSUME nor PREDICT.");
  }
}

void ForgetDirective(size_t directive_id) {
  // throw std::runtime_error("Forget does not work.");

  if (directives.count(directive_id) == 0) {
    throw std::runtime_error("There is no such directive.");
  }

  if (directives.size() == 1)
  {
    ClearRIPL();
  } else {
    // Check for ASSUME.
    // DeleteBranch(directives[directive_id].directive_node, false);
    if (directives[directive_id].directive_node->GetNodeType() == DIRECTIVE_OBSERVE) {
      UnconstrainBranch(dynamic_pointer_cast<NodeDirectiveObserve>(directives[directive_id].directive_node)->expression, 1, shared_ptr<ReevaluationParameters>());
    }
    directives.erase(directive_id);
  }
}

void RejectionSamplingForObserve() {
  map<size_t, directive_entry__only_expression> old_directives;

  for (map<size_t, directive_entry>::iterator directive = directives.begin();
        directive != directives.end();
        directive++)
  {
    old_directives[directive->first].node_type = directive->second.directive_node->GetNodeType();
    old_directives[directive->first].directive_as_string = directive->second.directice_as_string;
    if (old_directives[directive->first].node_type == DIRECTIVE_ASSUME) {
      old_directives[directive->first].name =
        dynamic_pointer_cast<NodeDirectiveAssume>(directive->second.directive_node)->name;
      old_directives[directive->first].original_expression =
        dynamic_pointer_cast<NodeDirectiveAssume>(directive->second.directive_node)->original_expression;
    } else if (old_directives[directive->first].node_type == DIRECTIVE_PREDICT) {
      old_directives[directive->first].original_expression =
        dynamic_pointer_cast<NodeDirectivePredict>(directive->second.directive_node)->original_expression;
    } else if (old_directives[directive->first].node_type == DIRECTIVE_OBSERVE) {
      old_directives[directive->first].original_expression =
        dynamic_pointer_cast<NodeDirectiveObserve>(directive->second.directive_node)->original_expression;
      old_directives[directive->first].observed_value =
        dynamic_pointer_cast<NodeDirectiveObserve>(directive->second.directive_node)->observed_value;
    } else {
      throw std::runtime_error("Unknown directive (1).");
    }
  }

  time_t starting_time = time(NULL);

  size_t number_of_rejecting_sampling_iterations = 0;

  while (true) {
    number_of_rejecting_sampling_iterations++;

    ClearRIPL();

    if (time(NULL) - starting_time > VENTURECONSTANT__MAX_ALLOWED_NUMBER_OF_SECONDS_FOR_REJECTION_SAMPLING) {
      throw std::runtime_error("Rejection sampling has not successfully found any suitable state within " + boost::lexical_cast<string>(VENTURECONSTANT__MAX_ALLOWED_NUMBER_OF_SECONDS_FOR_REJECTION_SAMPLING) + " second(s), made iterations: " + boost::lexical_cast<string>(number_of_rejecting_sampling_iterations) + ".");
    }

    bool unsatisfied_constraint = false;

    for (map<size_t, directive_entry__only_expression>::iterator old_directive = old_directives.begin();
         old_directive != old_directives.end();
         old_directive++)
    {
      last_directive_id = old_directive->first - 1;
      if (old_directive->second.node_type == DIRECTIVE_ASSUME) {
        unsatisfied_constraint =
          ExecuteDirective(old_directive->second.directive_as_string,
                           shared_ptr<NodeEvaluation>(new NodeDirectiveAssume(old_directive->second.name, AnalyzeExpression(old_directive->second.original_expression))),
                           old_directive->second.original_expression);
      } else if (old_directive->second.node_type == DIRECTIVE_PREDICT) {
        unsatisfied_constraint =
          ExecuteDirective(old_directive->second.directive_as_string,
                           shared_ptr<NodeEvaluation>(new NodeDirectivePredict(AnalyzeExpression(old_directive->second.original_expression))),
                           old_directive->second.original_expression);
      } else if (old_directive->second.node_type == DIRECTIVE_OBSERVE) {
        unsatisfied_constraint =
          ExecuteDirective(old_directive->second.directive_as_string,
                           shared_ptr<NodeEvaluation>(new NodeDirectiveObserve(AnalyzeExpression(old_directive->second.original_expression), old_directive->second.observed_value)),
                           old_directive->second.original_expression);
      } else {
        throw std::runtime_error("Unknown directive (1).");
      }

      if (unsatisfied_constraint == true) {
        break;
      }
    }
    
    if (unsatisfied_constraint == false) {
      return;
    }
  }
}

bool ExecuteDirective(string& directive_as_string,
                        shared_ptr<NodeEvaluation> directive_node,
                        shared_ptr<VentureValue> original_expression) {
  //shared_ptr<NodeEvaluation> last_directive_node;
  //if (directives.size() > 0) {
  //  last_directive_node = GetLastDirectiveNode();
  //}
  
  if (directive_node->GetNodeType() == DIRECTIVE_ASSUME) {
    shared_ptr<NodeDirectiveAssume> current_directive =
      dynamic_pointer_cast<NodeDirectiveAssume>(directive_node);
    current_directive->original_expression = original_expression;
  } else if (directive_node->GetNodeType() == DIRECTIVE_PREDICT) {
    shared_ptr<NodeDirectivePredict> current_directive =
      dynamic_pointer_cast<NodeDirectivePredict>(directive_node);
    current_directive->original_expression = original_expression;
  } else if (directive_node->GetNodeType() == DIRECTIVE_OBSERVE) {
    shared_ptr<NodeDirectiveObserve> current_directive =
      dynamic_pointer_cast<NodeDirectiveObserve>(directive_node);
    current_directive->original_expression = original_expression;
  } else {
    throw std::runtime_error("Unknown directive (2).");
  }

  last_directive_id++;
  directives.insert(pair<size_t, directive_entry>(last_directive_id, directive_entry(directive_as_string, directive_node)));

  EvaluationConfig tmp_evaluation_config(false, shared_ptr<ReevaluationParameters>());
  Evaluator(directive_node,
            global_environment,
            shared_ptr<Node>(),
            shared_ptr<NodeEvaluation>(),
            tmp_evaluation_config,
            "");
  // directive_node->earlier_evaluation_nodes = last_directive_node;
  
  return tmp_evaluation_config.unsatisfied_constraint;
}

size_t ExecuteDirectiveWithRejectionSampling
(string& directive_as_string,
 shared_ptr<NodeEvaluation> directive_node,
 shared_ptr<VentureValue> original_expression) {
  bool unsatisfied_constraint = ExecuteDirective(directive_as_string, directive_node, original_expression);

  if (unsatisfied_constraint == true) {
    RejectionSamplingForObserve();
    // throw std::runtime_error("You are trying to execute the code, which has the joint score = 0.0 (at least in one of its state!).");
  }

  return directives.rbegin()->first;
}

void BindStandardElementsToGlobalEnvironment() {

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("load_remote_xrp")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__LoadRemoteXRP()))));
#endif

  // Deprecated, should be deleted:
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("compare_images")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__CompareImages()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("new_set")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__NewSet()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("add_to_set")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__AddToSet()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("sample_from_set")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__SampleFromSet()))));

  // Makers of XRPs with internal state.
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("crp_make")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__CRPmaker()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("mem")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__memoizer()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("symmetric_dirichlet_multinomial_make")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__SymmetricDirichletMultinomial_maker()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("dirichlet_multinomial_make")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__DirichletMultinomial_maker()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("beta_binomial_make")), // Make just via the std::string?
                                                                                        // FIXME: add check that there are 2 arguments!
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__DirichletMultinomial_maker()))));

  // Elementary random procedures.
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("flip")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Flip()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("bernoulli")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Flip()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("binomial")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Binomial()))));
  // WARNING: Deprecated:
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("noise_negate")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__NoisyNegate()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("noisy_negate")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__NoisyNegate()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("condition_erp")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__ConditionERP()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("normal")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Normal()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("beta")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Beta()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("poisson")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Poisson()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("gamma")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Gamma()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("inv_gamma")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__InverseGamma()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("chisq")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__ChiSquared()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("inv_chisq")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__InverseChiSquared()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("uniform_discrete")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__UniformDiscrete()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("uniform_continuous")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__UniformContinuous()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("categorical")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Categorical()))));
  
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("symmetric_dirichlet")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__SymmetricDirichlet()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("dirichlet")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__Dirichlet()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("+")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealPlus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("*")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealMultiply()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("-")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealMinus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("/")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealDivide()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("cos")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealCos()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("sin")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealSin()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("power")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealPower()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol(">=")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqualOrGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("<=")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqualOrLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol(">")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("<")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("=")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqual()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("inc")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Inc()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("dec")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Dec()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("equal")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Equal()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("not")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__BooleanNot()))));  

  // For reals (repeating)

  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_plus")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealPlus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_times")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealMultiply()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_minus")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealMinus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_div")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealDivide()))));

  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_gte")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqualOrGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_lte")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqualOrLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_gt")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_lt")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("real_eq")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RealEqual()))));

  // For integers

  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_plus")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerPlus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_times")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerMultiply()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_minus")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerMinus()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_div")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerDivide()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_mod")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerModulo()))));
  
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_gte")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerEqualOrGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_lte")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerEqualOrLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_gt")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerGreater()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_lt")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerLesser()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_eq")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerEqual()))));
  
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_ls")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerLeftShift()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_rs")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerRightShift()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_and")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerAnd()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_or")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerOr()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_xor")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerXor()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("int_not")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__IntegerNot()))));
  
  // List and related procedures (should become deprecated soon, when we introduce new basic data type to Venture).
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("list")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__List()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("first")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__First()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("rest")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Rest()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("cons")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Cons()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("length")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Length()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("empty?")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__EmptyQUESTIONMARK()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("nth")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__Nth()))));
  
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("scv+scv")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__SCVPlusSCV()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("scv*scalar")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__SCVMultiplyScalar()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("scv")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__SCV()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("repeat-scv")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__RepeatSCV()))));
  
  // Types casting.
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("simplex_point")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__SimplexPoint()))));
                    
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("get_letter_id")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__GetLetterId()))));
                    
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("load_python_Shell_module")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive_LoadPythonShellModule()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("generate_empty_surface_and_pmap_prior")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__GenerateEmptySurfaceAndPMapPrior()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("update_pmap_and_add_lobe")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__UpdatePMapAndAddLobe()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("get_lobe_pos_x")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__GetLobePosX()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("get_lobe_pos_y")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__GetLobePosY()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("noisy_drill_well")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new ERP__NoisyDrillWell()))));
                    
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("load-matlab-function")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__LoadMATLABFunction()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("load-python-function")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new Primitive__LoadPythonFunction()))));
  BindToEnvironment(global_environment,
                    shared_ptr<VentureSymbol>(new VentureSymbol("gensym")), // Make just via the std::string?
                    shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__Gensym()))));
}





real GetLogscoreOfDirective(shared_ptr<Node> first_node) {
  real changed_probability = log(1.0);
  queue< shared_ptr<Node> > processing_queue;
  processing_queue.push(first_node);
  while (!processing_queue.empty()) {
    processing_queue.front()->GetChildren(processing_queue);
    shared_ptr<Node> current_node = processing_queue.front();
    processing_queue.pop();

    if (current_node->GetNodeType() == XRP_APPLICATION) {
      shared_ptr<NodeXRPApplication> current_node2 = dynamic_pointer_cast<NodeXRPApplication>(current_node);

      vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(current_node2->environment, // Not efficient?
                                      dynamic_pointer_cast<NodeEvaluation>(current_node2), true);
      
      if (current_node2->evaluated == false) {
        throw std::runtime_error("Removing from unevaluated!");
      }

      current_node2->xrp->xrp->Remove(got_arguments, current_node2->my_sampled_value);
      changed_probability += current_node2->xrp->xrp->GetSampledLoglikelihood(got_arguments, current_node2->my_sampled_value);

      if (current_node->GetNodeType() == XRP_APPLICATION &&
            dynamic_pointer_cast<NodeXRPApplication>(current_node)->xrp->xrp->GetName() == "XRP__memoized_procedure")
      {
        string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(got_arguments);
        XRP__memoizer_map_element& mem_table_element =
          (*(dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<NodeXRPApplication>(current_node)->xrp->xrp)->mem_table.find(mem_table_key))).second;
        if (mem_table_element.active_uses == 0) {
          processing_queue.push(mem_table_element.application_caller_node);
        }
      }
    }
  }
  return changed_probability;
}

void RestoreDirective(shared_ptr<Node> first_node) {
  queue< shared_ptr<Node> > processing_queue;
  processing_queue.push(first_node);
  while (!processing_queue.empty()) {
    processing_queue.front()->GetChildren(processing_queue);
    shared_ptr<Node> current_node = processing_queue.front();
    processing_queue.pop();

    if (current_node->GetNodeType() == XRP_APPLICATION) {
      shared_ptr<NodeXRPApplication> current_node2 = dynamic_pointer_cast<NodeXRPApplication>(current_node);

      vector< shared_ptr<VentureValue> > got_arguments = GetArgumentsFromEnvironment(current_node2->environment, // Not efficient?
                                      dynamic_pointer_cast<NodeEvaluation>(current_node2), true);
      
      current_node2->xrp->xrp->Incorporate(got_arguments, current_node2->my_sampled_value);

      if (current_node->GetNodeType() == XRP_APPLICATION &&
            dynamic_pointer_cast<NodeXRPApplication>(current_node)->xrp->xrp->GetName() == "XRP__memoized_procedure")
      {
        string mem_table_key = XRP__memoized_procedure__MakeMapKeyFromArguments(got_arguments);
        XRP__memoizer_map_element& mem_table_element =
          (*(dynamic_pointer_cast<XRP__memoized_procedure>(dynamic_pointer_cast<NodeXRPApplication>(current_node)->xrp->xrp)->mem_table.find(mem_table_key))).second;
        if (mem_table_element.active_uses == 1) {
          processing_queue.push(mem_table_element.application_caller_node);
        }
      }
    }
  }
  return;
}

real GetLogscoreOfAllDirectives() {
  real changed_probability = log(1.0);
  
  for (map<size_t, directive_entry>::iterator iterator = directives.begin(); iterator != directives.end(); iterator++) {
    changed_probability += GetLogscoreOfDirective(iterator->second.directive_node);
  }
  for (map<size_t, directive_entry>::iterator iterator = directives.begin(); iterator != directives.end(); iterator++) {
    RestoreDirective(iterator->second.directive_node);
  }

  return changed_probability;
}
