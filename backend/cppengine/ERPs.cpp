#include "HeaderPre.h"
#include "ERPs.h"

void ERP::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                  shared_ptr<VentureValue> sampled_value) { // inline?

}
void ERP::Remove(vector< shared_ptr<VentureValue> >& arguments,
            shared_ptr<VentureValue> sampled_value) { // inline?

}

bool ERP::IsRandomChoice() { return true; }
bool ERP::CouldBeRescored() { return true; }
string ERP::GetName() { return "ERPClass"; }
  
real ERP__Flip::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                shared_ptr<VentureValue> sampled_value) { // inline?
  real weight;
  if (arguments.size() == 0) {
    weight = 0.5;
  } else if (arguments.size() == 1) {
    VentureProbability::CheckMyData(arguments[0].get());
    weight = arguments[0]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  if (VerifyVentureType<VentureBoolean>(sampled_value) == true) {
    if (CompareValue(sampled_value, shared_ptr<VentureValue>(new VentureBoolean(true)))) {
      return log(weight);
    } else {
      return log(1.0 - weight);
    }
  } else {
    //cout << " " << sampled_value << endl;
    throw std::runtime_error("Wrong value.");
  }
}
shared_ptr<VentureValue> ERP__Flip::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  real weight;
  if (arguments.size() == 0) {
    weight = 0.5;
  } else if (arguments.size() == 1) {
    VentureProbability::CheckMyData(arguments[0].get());
    weight = arguments[0]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  unsigned int result_int = gsl_ran_bernoulli(random_generator, weight);
  bool result_bool = (result_int == 1);
  return shared_ptr<VentureBoolean>(new VentureBoolean(result_bool));
}
string ERP__Flip::GetName() { return "ERP__Flip"; }

real ERP__Binomial::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                shared_ptr<VentureValue> sampled_value) { // inline?
  real weight;
  int number_of_attempts;
  if (arguments.size() == 2) {
    VentureCount::CheckMyData(arguments[0].get());
    number_of_attempts = arguments[0]->GetInteger();
    VentureProbability::CheckMyData(arguments[1].get());
    weight = arguments[1]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int number_of_successes = sampled_value->GetInteger();
  if (number_of_successes > number_of_attempts) {
    return log(0.0);                
  } else {
    return
      gsl_sf_lngamma(number_of_attempts + 1) -
      (gsl_sf_lngamma(number_of_attempts - number_of_successes + 1) +
      gsl_sf_lngamma(number_of_successes + 1)) + log(weight) * number_of_successes +
      log(1 - weight) * (number_of_attempts - number_of_successes);
  }
}
shared_ptr<VentureValue> ERP__Binomial::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  real weight;
  int number_of_attempts;
  if (arguments.size() == 2) {
    VentureCount::CheckMyData(arguments[0].get());
    number_of_attempts = arguments[0]->GetInteger();
    VentureProbability::CheckMyData(arguments[1].get());
    weight = arguments[1]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return shared_ptr<VentureCount>(new VentureCount(gsl_ran_binomial(random_generator, weight, number_of_attempts)));
}
string ERP__Binomial::GetName() { return "ERP__Binomial"; }

real ERP__Normal::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 2) {
    VentureReal::CheckMyData(arguments[0].get());
    real average = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real sigma = arguments[1]->GetReal();
    //double likelihood =
    //       gsl_ran_gaussian_pdf(ToVentureType<VentureReal>(sampled_value)->GetReal() - // Should be ToVentureType<VentureReal>(sampled_value) in a good way.
    //                              average,
    //                            sigma);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return NormalDistributionLogLikelihood(sampled_value_real, average, sigma);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__Normal::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 2) {
    VentureReal::CheckMyData(arguments[0].get());
    real average = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real sigma = arguments[1]->GetReal();
    double random_value =
           gsl_ran_gaussian(random_generator, sigma) + average;
    return shared_ptr<VentureReal>(new VentureReal(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__Normal::GetName() { return "ERP__Normal"; }
bool ERP__Normal::CouldBeSliceSampled() {
  return true;
}

real ERP__Beta::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    //double likelihood =
    //       gsl_ran_beta_pdf(ToVentureType<VentureReal>(sampled_value)->GetReal(),
    //                        alpha,
    //                        beta);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return BetaDistributionLogLikelihood(sampled_value_real, alpha, beta);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__Beta::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    double random_value = gsl_ran_beta(random_generator, alpha, beta);
    return shared_ptr<VentureReal>(new VentureReal(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__Beta::GetName() { return "ERP__Beta"; }

real ERP__Poisson::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real lambda = arguments[0]->GetReal();
    //double likelihood =
    //       gsl_ran_poisson_pdf(ToVentureType<VentureCount>(sampled_value)->GetInteger(),
    //                         lambda);
    //return log(likelihood);
    int sampled_value_count = sampled_value->GetInteger();
    return PoissonDistributionLogLikelihood(sampled_value_count, lambda);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__Poisson::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real lambda = arguments[0]->GetReal();
    int random_value = gsl_ran_poisson(random_generator, lambda);
    return shared_ptr<VentureCount>(new VentureCount(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__Poisson::GetName() { return "ERP__Poisson"; }

real ERP__Gamma::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    //double likelihood =
    //       gsl_ran_gamma_pdf(ToVentureType<VentureReal>(sampled_value)->GetReal(),
    //                         alpha,
    //                         1.0 / beta);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return GammaDistributionLogLikelihood(sampled_value_real, alpha, beta);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__Gamma::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    double random_value =
           gsl_ran_gamma(random_generator, alpha, 1.0 / beta);
    return shared_ptr<VentureReal>(new VentureReal(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__Gamma::GetName() { return "ERP__Gamma"; }

real ERP__InverseGamma::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    //double likelihood =
    //       gsl_ran_gamma_pdf(1.0 / ToVentureType<VentureReal>(sampled_value)->GetReal(),
    //                         alpha,
    //                         1.0 / beta);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return InverseGammaDistributionLogLikelihood(sampled_value_real, alpha, beta);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__InverseGamma::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 2) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    VentureSmoothedCount::CheckMyData(arguments[1].get());
    real beta = arguments[1]->GetReal();
    double random_value =
           gsl_ran_gamma(random_generator,
                         alpha,
                         1.0 / beta);
    return shared_ptr<VentureReal>(new VentureReal(1.0 / random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__InverseGamma::GetName() { return "ERP__InverseGamma"; }

real ERP__ChiSquared::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real nu = arguments[0]->GetReal();
    //double likelihood =
    //       gsl_ran_chisq_pdf(ToVentureType<VentureReal>(sampled_value)->GetReal(),
    //                         nu);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return ChiSquaredDistributionLogLikelihood(sampled_value_real, nu);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__ChiSquared::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real nu = arguments[0]->GetReal();
    double random_value =
           gsl_ran_chisq(random_generator,
                         nu);
    return shared_ptr<VentureReal>(new VentureReal(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__ChiSquared::GetName() { return "ERP__ChiSquared"; }

real ERP__InverseChiSquared::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real nu = arguments[0]->GetReal();
    //double likelihood =
    //       gsl_ran_chisq_pdf(1.0 / ToVentureType<VentureReal>(sampled_value)->GetReal(),
    //                         nu);
    //return log(likelihood);
    real sampled_value_real = sampled_value->GetReal();
    return InverseChiSquaredDistributionLogLikelihood(sampled_value_real, nu);
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__InverseChiSquared::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 1) {
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real nu = arguments[0]->GetReal();
    double random_value =
           gsl_ran_chisq(random_generator,
                         nu);
    return shared_ptr<VentureReal>(new VentureReal(1.0 / random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__InverseChiSquared::GetName() { return "ERP__InverseChiSquared"; }

real ERP__SymmetricDirichlet::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 2) {
    VentureCount::CheckMyData(arguments[1].get());
    size_t dimensionality = arguments[1]->GetInteger();
    vector<real>& sampled_simplex_point = ToVentureType<VentureSimplexPoint>(sampled_value)->data;
    assert(dimensionality == sampled_simplex_point.size());
    
    double* arguments_for_gsl = new double[dimensionality];
    double* returned_values = new double[dimensionality];
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    double alpha = arguments[0]->GetReal();

    for (size_t index = 0; index < dimensionality; index++) {
      arguments_for_gsl[index] = alpha;
      returned_values[index] = sampled_simplex_point[index];
    }

    real loglikelihood = gsl_ran_dirichlet_lnpdf(dimensionality, arguments_for_gsl, returned_values);
    
    delete [] arguments_for_gsl;
    delete [] returned_values;

    return loglikelihood;
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__SymmetricDirichlet::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 2) {
    VentureCount::CheckMyData(arguments[1].get());
    size_t dimensionality = arguments[1]->GetInteger();
    double* arguments_for_gsl = new double[dimensionality];
    double* returned_values = new double[dimensionality];
    VentureSmoothedCount::CheckMyData(arguments[0].get());
    real alpha = arguments[0]->GetReal();
    for (size_t index = 0; index < dimensionality; index++) {
      arguments_for_gsl[index] = alpha;
    }

    gsl_ran_dirichlet(random_generator, dimensionality, arguments_for_gsl, returned_values);
    
    vector<real> returned_value_as_vector(returned_values, returned_values + dimensionality);
    
    delete [] arguments_for_gsl;
    delete [] returned_values;
    
    return shared_ptr<VentureSimplexPoint>(new VentureSimplexPoint(returned_value_as_vector));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__SymmetricDirichlet::GetName() { return "ERP__SymmetricDirichlet"; }

real ERP__Dirichlet::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) {
  if (arguments.size() == 0)
  {
    throw std::runtime_error("Wrong number of arguments.");
  }
  
  size_t dimensionality;
  if (arguments[0]->GetType() == SMOOTHED_COUNT_VECTOR) {
    if (arguments.size() != 1)
    {
      throw std::runtime_error("Wrong number of arguments.");
    }
    dimensionality = ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size();
  } else {
    if (arguments.size() < 2) {
      throw std::runtime_error("Wrong number of arguments.");
    }
    dimensionality = arguments.size();
  }
  
  // After this line no exceptions should happen!
  double* arguments_for_gsl = new double[dimensionality];
  if (arguments[0]->GetType() == SMOOTHED_COUNT_VECTOR) {
    for (size_t index = 0; index < dimensionality; index++) {
      arguments_for_gsl[index] = ToVentureType<VentureSmoothedCountVector>(arguments[0])->data[index];
    }
  } else {
    for (size_t index = 0; index < dimensionality; index++) {
      VentureSmoothedCount::CheckMyData(arguments[index].get());
      arguments_for_gsl[index] = arguments[index]->GetReal();
    }
  }
  
  vector<real>& sampled_simplex_point = ToVentureType<VentureSimplexPoint>(sampled_value)->data;
  assert(dimensionality == sampled_simplex_point.size());
  double* returned_values = new double[dimensionality];

  for (size_t index = 0; index < dimensionality; index++) {
    returned_values[index] = sampled_simplex_point[index];
  }

  real loglikelihood = gsl_ran_dirichlet_lnpdf(dimensionality, arguments_for_gsl, returned_values);
  
  delete [] arguments_for_gsl;
  delete [] returned_values;

  return loglikelihood;
}
shared_ptr<VentureValue> ERP__Dirichlet::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 0)
  {
    throw std::runtime_error("Wrong number of arguments.");
  }
  
  size_t dimensionality;
  if (arguments[0]->GetType() == SMOOTHED_COUNT_VECTOR) {
    if (arguments.size() != 1)
    {
      throw std::runtime_error("Wrong number of arguments.");
    }
    dimensionality = ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size();
  } else {
    if (arguments.size() < 2) {
      throw std::runtime_error("Wrong number of arguments.");
    }
    dimensionality = arguments.size();
  }

  // After this line no exceptions should happen!
  double* arguments_for_gsl = new double[dimensionality];
  if (arguments[0]->GetType() == SMOOTHED_COUNT_VECTOR) {
    for (size_t index = 0; index < dimensionality; index++) {
      arguments_for_gsl[index] = ToVentureType<VentureSmoothedCountVector>(arguments[0])->data[index];
    }
  } else {
    for (size_t index = 0; index < dimensionality; index++) {
      VentureSmoothedCount::CheckMyData(arguments[index].get());
      arguments_for_gsl[index] = arguments[index]->GetReal();
    }
  }
 
  double* returned_values = new double[dimensionality];
 
  gsl_ran_dirichlet(random_generator, dimensionality, arguments_for_gsl, returned_values);
  
  vector<real> returned_value_as_vector(returned_values, returned_values + dimensionality);
  
  delete [] arguments_for_gsl;
  delete [] returned_values;

  return shared_ptr<VentureSimplexPoint>(new VentureSimplexPoint(returned_value_as_vector));
}
string ERP__Dirichlet::GetName() { return "ERP__Dirichlet"; }

real ERP__Categorical::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<VentureValue> sampled_value) { // inline?
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureSimplexPoint> simplex_point = ToVentureType<VentureSimplexPoint>(arguments[0]);
  size_t index = sampled_value->GetInteger();
  if (index < 0 || index >= simplex_point->data.size()) {
    /*
    We do not throw exception here, because this Venture code should be valid:

    ASSUME size (uniform-discrete 1 10)
    ASSUME my-simplex-point (create-simplex-point-uniformly size)
    ASSUME my-variable (categorical-sp my-simplex-point)

    Let's imagine:
    1) size was 10, and my-variable was 10,
    2) then during the step of MH inference we repropose size to be 5,
    3) engine rescores the (categorical-sp ...) with old and new my-simplex-point,
       and P(new) should be equal to 0, because my-variable is equal to 10.
    */
    return log(0.0);
  } else {
    return log(simplex_point->data[index]);
  }
}
shared_ptr<VentureValue> ERP__Categorical::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  double random_uniform_0_1 = gsl_ran_flat(random_generator, 0, 1);
  shared_ptr<VentureSimplexPoint> simplex_point = ToVentureType<VentureSimplexPoint>(arguments[0]);
  double accumulated_probability = 0.0;

  for (size_t index = 0; index < simplex_point->data.size(); index++) {
    accumulated_probability += simplex_point->data[index];
    if (random_uniform_0_1 <= accumulated_probability) {
      return shared_ptr<VentureAtom>(new VentureAtom(index));
    }
  }
  
  throw std::runtime_error("Probabilities do not sum to 1.0 (you should not see this error :) ).");
  // This should not happen, because SimplexPoint should has preverified the invariant
  // that sum is equal to 1.0.
  // If somebody has this exception, something strange happens,
  // and user should know that it is very strange.
}
string ERP__Categorical::GetName() { return "ERP__Categorical"; }

real ERP__UniformDiscrete::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value) {
  int left_bound;
  int right_bound;
  if (arguments.size() == 2) {
    assert(arguments[1]->GetInteger() >= arguments[0]->GetInteger());
    VentureCount::CheckMyData(arguments[0].get()); // Should be on! Just for the curve fitting!
    left_bound = arguments[0]->GetInteger(); // Should be GetInteger! Just for the curve fitting!
    VentureCount::CheckMyData(arguments[1].get()); // Should be on! Just for the curve fitting!
    right_bound = arguments[1]->GetInteger(); // Should be GetInteger! Just for the curve fitting!
    if (sampled_value->GetInteger() >= left_bound &&
      sampled_value->GetInteger() <= right_bound) {
      return log(1.0 / (1.0 + right_bound - left_bound));
    } else {
      return log(0.0);
    }
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__UniformDiscrete::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  int left_bound;
  int right_bound;
  if (arguments.size() == 2) {
    assert(arguments[1]->GetInteger() >= arguments[0]->GetInteger());
    VentureCount::CheckMyData(arguments[0].get()); // Should be on! Just for the curve fitting!
    left_bound = arguments[0]->GetInteger(); // Should be GetInteger! Just for the curve fitting!
    VentureCount::CheckMyData(arguments[1].get()); // Should be on! Just for the curve fitting!
    right_bound = arguments[1]->GetInteger(); // Should be GetInteger! Just for the curve fitting!
    int random_value = UniformDiscrete(left_bound, right_bound);
    return shared_ptr<VentureCount>(new VentureCount(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__UniformDiscrete::GetName() { return "ERP__UniformDiscrete"; }

real ERP__UniformContinuous::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value) {
  real left_bound;
  real right_bound;
  if (arguments.size() == 2) {
    assert(arguments[1]->GetReal() >= arguments[0]->GetReal());
    VentureReal::CheckMyData(arguments[0].get());
    left_bound = arguments[0]->GetReal();
    VentureReal::CheckMyData(arguments[1].get());
    right_bound = arguments[1]->GetReal();
    if (sampled_value->GetReal() >= left_bound &&
      sampled_value->GetReal() <= right_bound) {
      return log(1.0 / (right_bound - left_bound));
    } else {
      return log(0.0);
    }
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__UniformContinuous::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  real left_bound;
  real right_bound;
  if (arguments.size() == 2) {
    assert(arguments[1]->GetReal() >= arguments[0]->GetReal());
    VentureReal::CheckMyData(arguments[0].get());
    left_bound = arguments[0]->GetReal();
    VentureReal::CheckMyData(arguments[1].get());
    right_bound = arguments[1]->GetReal();
    double random_value =
          gsl_ran_flat(random_generator,
                         left_bound,
                         right_bound);
    return shared_ptr<VentureReal>(new VentureReal(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__UniformContinuous::GetName() { return "ERP__UniformContinuous"; }
bool ERP__UniformContinuous::CouldBeSliceSampled() {
  return true;
}

real ERP__NoisyNegate::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                shared_ptr<VentureValue> sampled_value) { // inline?
  bool boolean_expression;
  real weight;
  if (arguments.size() == 2) {
    boolean_expression = ToVentureType<VentureBoolean>(arguments[0])->data;
    VentureProbability::CheckMyData(arguments[1].get());
    weight = arguments[1]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  if (VerifyVentureType<VentureBoolean>(arguments[0]) == true) {
    if (CompareValue(sampled_value, shared_ptr<VentureValue>(new VentureBoolean(boolean_expression)))) {
      return log(1.0 - weight);
    } else {
      return log(weight);
    }
  } else {
    //cout << " " << sampled_value << endl;
    throw std::runtime_error("Wrong value.");
  }
}
shared_ptr<VentureValue> ERP__NoisyNegate::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  bool boolean_expression;
  real weight;
  if (arguments.size() == 2) {
    boolean_expression = ToVentureType<VentureBoolean>(arguments[0])->data;
    VentureProbability::CheckMyData(arguments[1].get());
    weight = arguments[1]->GetReal();
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
  unsigned int result_int = gsl_ran_bernoulli(random_generator, weight);
  if (result_int == 1) {
    return shared_ptr<VentureBoolean>(new VentureBoolean(!boolean_expression));
  } else {
    return shared_ptr<VentureBoolean>(new VentureBoolean(boolean_expression));
  }
}
string ERP__NoisyNegate::GetName() { return "ERP__NoisyNegate"; }

real ERP__ConditionERP::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                                shared_ptr<VentureValue> sampled_value) { // inline?
  if (arguments.size() != 3) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  if (StandardPredicate(arguments[0]) &&
      arguments[1].get() == sampled_value.get()) { // Comparing by reference.
    return log(1.0);
  } else if (!StandardPredicate(arguments[0])
              && arguments[2].get() == sampled_value.get()) { // Comparing by reference.
    return log(1.0);
  } else {
    return log(0.0);
  }
}
shared_ptr<VentureValue> ERP__ConditionERP::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 3) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  if (StandardPredicate(arguments[0])) {
    return arguments[1];
  } else {
    return arguments[2];
  }
}
  
bool ERP__ConditionERP::IsRandomChoice() { return false; }
bool ERP__ConditionERP::CouldBeRescored() { return false; }
string ERP__ConditionERP::GetName() { return "ERP__ConditionERP"; }

real ERP__CompareImages::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                                shared_ptr<VentureValue> sampled_value) { // inline?
  int digit_id_1 = arguments[0]->GetInteger() / 10000;
  int digit_id_2 = arguments[1]->GetInteger() / 10000;
  int instance_1 = arguments[0]->GetInteger() % 10000;
  int instance_2 = arguments[1]->GetInteger() % 10000;
  real offset_x = arguments[2]->GetReal();
  real offset_y = arguments[3]->GetReal();
  real rotate_angle = arguments[4]->GetReal();
  real noise = arguments[5]->GetReal();
  
  real loglikelihood = 0;
  for (char x = 0; x < 28; x++) {
    for (char y = 0; y < 28; y++) {
      int new_x = ((x + offset_x) * cos(rotate_angle) - (y + offset_y) * sin(rotate_angle));
      int new_y = ((y + offset_y) * cos(rotate_angle) + (x + offset_x) * sin(rotate_angle));

      char color;
      if (new_x < 0 || new_x >= 28 || new_y < 0 || new_y >= 28) {
        color = 0;
      } else {
        // color = digits[digit_id_2][instance_2][new_x][new_y];
      }
      if (arguments[0]->GetInteger() == arguments[1]->GetInteger()) {
        // loglikelihood += NormalDistributionLoglikelihood(digits[digit_id_1][instance_1][x][y] + 100, 0, noise);
      } else {
        // loglikelihood += NormalDistributionLoglikelihood(static_cast<int>(digits[digit_id_1][instance_1][x][y]) - static_cast<int>(color), 0, noise);
      }
    }
  }
  return loglikelihood;
}
shared_ptr<VentureValue> ERP__CompareImages::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  return shared_ptr<VentureBoolean>(new VentureBoolean(true));
}
bool ERP__CompareImages::IsRandomChoice() { return true; }
bool ERP__CompareImages::CouldBeRescored() { return true; }
string ERP__CompareImages::GetName() { return "ERP__CompareImages"; }

real ERP__GetLetterId::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value) {
  int left_bound = 0;
  int right_bound = 4;
  if (arguments.size() == 0) {
    if (ToVentureType<VentureCount>(sampled_value)->GetInteger() >= left_bound &&
      ToVentureType<VentureCount>(sampled_value)->GetInteger() <= right_bound) {
      return log(1.0 / (1.0 + right_bound - left_bound));
    } else {
      return log(0.0);
    }
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
shared_ptr<VentureValue> ERP__GetLetterId::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  int left_bound = 0;
  int right_bound = 4;
  if (arguments.size() == 0) {
    int random_value = UniformDiscrete(left_bound, right_bound);
    return shared_ptr<VentureCount>(new VentureCount(random_value));
  } else {
    throw std::runtime_error("Wrong number of arguments.");
  }
}
string ERP__GetLetterId::GetName() { return "ERP__GetLetterId"; }
bool ERP__GetLetterId::CouldBeEnumerated() {
  return true;
}
set< shared_ptr<VentureValue> > ERP__GetLetterId::EnumeratingSupport() { // FIXME: pass the *result* by reference, not by value.
  set< shared_ptr<VentureValue> > returning_set;
  for (size_t index = 0; index <= 4; index++) {
    returning_set.insert(shared_ptr<VentureCount>(new VentureCount(index)));
  }
  return returning_set;
}
