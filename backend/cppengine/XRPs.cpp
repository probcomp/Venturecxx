#include "HeaderPre.h"
#include "XRPs.h"

// CRPmaker
shared_ptr<VentureValue> XRP__CRPmaker::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  VentureSmoothedCount::CheckMyData(arguments[0].get());

  shared_ptr<XRP> new_xrp = shared_ptr<XRP>(new XRP__CRPsampler()); // If we put here XRP__CRPmaker() (it is stupid, but nevertheless), it raises some memory error. Why?
  // Should be done on the line above (through the XRP__CRPsampler constructor!):
  dynamic_pointer_cast<XRP__CRPsampler>(new_xrp)->alpha = arguments[0]->GetReal();
  dynamic_pointer_cast<XRP__CRPsampler>(new_xrp)->current_number_of_clients = 0;
  return shared_ptr<VentureXRP>(new VentureXRP(new_xrp));
}

real XRP__CRPmaker::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0); // ?
}

void XRP__CRPmaker::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
}

void XRP__CRPmaker::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
}
bool XRP__CRPmaker::IsRandomChoice() { return false; }
bool XRP__CRPmaker::CouldBeRescored() { return false; }
string XRP__CRPmaker::GetName() { return "XRP__CRPmaker"; }

// CRPsampler
shared_ptr<VentureValue> XRP__CRPsampler::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  // FIXME: rewrite with SampleCategorical(...).
  if (arguments.size() != 0) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  double random_uniform_0_1 = gsl_ran_flat(random_generator, 0, 1);
  double accumulated_probability = 0.0;
  double expected_sum = this->alpha +
                          this->current_number_of_clients;
  for (map<int, size_t>::const_iterator iterator = this->atoms.begin();
         iterator != this->atoms.end();
         iterator++) {
    accumulated_probability += static_cast<double>((*iterator).second) / expected_sum;
    if (random_uniform_0_1 <= accumulated_probability) {
      return shared_ptr<VentureAtom>(new VentureAtom((*iterator).first));
    }
  }

  int next_free_index = 0;
  while (this->atoms.count(next_free_index) != 0) {
    next_free_index++;
  }
  return shared_ptr<VentureAtom>(new VentureAtom(next_free_index));

  next_gensym_atom++;
  // cout << "Resampling XRP" << next_gensym_atom << endl;
  return shared_ptr<VentureAtom>(new VentureAtom(next_gensym_atom));
}

real XRP__CRPsampler::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  if (this->atoms.count(ToVentureType<VentureAtom>(sampled_value)->data) == 0) {
    // Not 100% true, but it is okay.
    return log(this->alpha /
                (this->alpha +
                  this->current_number_of_clients));
  } else {
    return log(this->atoms[ToVentureType<VentureAtom>(sampled_value)->data] /
                (this->alpha +
                  this->current_number_of_clients));
  }
}

void XRP__CRPsampler::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
  if (this->atoms.count(ToVentureType<VentureAtom>(sampled_value)->data) == 1) {
    this->atoms[ToVentureType<VentureAtom>(sampled_value)->data]++;
  } else {
    this->atoms[ToVentureType<VentureAtom>(sampled_value)->data] = 1;
  }
  this->current_number_of_clients++;
}

void XRP__CRPsampler::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
  if (this->atoms.count(ToVentureType<VentureAtom>(sampled_value)->data) == 0) {
    throw std::runtime_error("CRP statistics does not have this atom.");
  } else {
    this->atoms[ToVentureType<VentureAtom>(sampled_value)->data]--;
    if (this->atoms[ToVentureType<VentureAtom>(sampled_value)->data] == 0) {
      this->atoms.erase(ToVentureType<VentureAtom>(sampled_value)->data);
    }
  }
  this->current_number_of_clients--;
}
bool XRP__CRPsampler::IsRandomChoice() { return true; }
bool XRP__CRPsampler::CouldBeRescored() { return true; }
string XRP__CRPsampler::GetName() { return "XRP__CRPsampler"; }





// SymmetricDirichletMultinomial_maker
// Arguments:
// 1) alpha; smoothed count
// 2) dimensionality; count? (should be at least >= 2)
shared_ptr<VentureValue> XRP__SymmetricDirichletMultinomial_maker::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  VentureSmoothedCount::CheckMyData(arguments[0].get());
  VentureCount::CheckMyData(arguments[1].get());
  if (arguments[1]->GetInteger() < 1) {
    throw std::runtime_error("The second argument (the dimensionality) should be >= 2.");
  }

  shared_ptr<XRP> new_xrp = shared_ptr<XRP>(new XRP__DirichletMultinomial_sampler());
  // Should be done on the line above (through the XRP__DirichletMultinomial_sampler constructor!):
  dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(new_xrp)->statistics =
    vector<real>(arguments[1]->GetInteger(), arguments[0]->GetReal());
  dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(new_xrp)->sum_of_statistics =
    arguments[0]->GetReal() * arguments[1]->GetInteger();

  return shared_ptr<VentureXRP>(new VentureXRP(new_xrp));
}

real XRP__SymmetricDirichletMultinomial_maker::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0); // ?
}

void XRP__SymmetricDirichletMultinomial_maker::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
}

void XRP__SymmetricDirichletMultinomial_maker::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
}
bool XRP__SymmetricDirichletMultinomial_maker::IsRandomChoice() { return false; }
bool XRP__SymmetricDirichletMultinomial_maker::CouldBeRescored() { return false; }
string XRP__SymmetricDirichletMultinomial_maker::GetName() { return "XRP__SymmetricDirichletMultinomial_maker"; }

// DirichletMultinomial_maker
// Arguments:
// 1) list = (alpha1 ... alpha_k), k >= 2
shared_ptr<VentureValue> XRP__DirichletMultinomial_maker::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureList> list = ToVentureType<VentureList>(arguments[0]);
  if (GetSize(list) < 2) {
    throw std::runtime_error("The dimensionality should be >= 2.");
  }
  shared_ptr<XRP> new_xrp = shared_ptr<XRP>(new XRP__DirichletMultinomial_sampler());
  dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(new_xrp)->sum_of_statistics = 0.0;
  // Should be done on the line above (through the XRP__DirichletMultinomial_sampler constructor!):
  while (list != NIL_INSTANCE) {
    real new_element = list->car->GetReal();
    dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(new_xrp)->statistics.push_back(new_element);
    dynamic_pointer_cast<XRP__DirichletMultinomial_sampler>(new_xrp)->sum_of_statistics += new_element;
    list = GetNext(list);
  }
  return shared_ptr<VentureXRP>(new VentureXRP(new_xrp));
}

real XRP__DirichletMultinomial_maker::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0); // ?
}

void XRP__DirichletMultinomial_maker::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
}

void XRP__DirichletMultinomial_maker::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
}
bool XRP__DirichletMultinomial_maker::IsRandomChoice() { return false; }
bool XRP__DirichletMultinomial_maker::CouldBeRescored() { return false; }
string XRP__DirichletMultinomial_maker::GetName() { return "XRP__DirichletMultinomial_maker"; }

// DirichletMultinomial_sampler
/*
real XRP__DirichletMultinomial_sampler::GetSumOfStatistics() {
  real sum_of_statistics = 0.0;
  for (size_t index = 0; index < this->statistics.size(); index++) {
    sum_of_statistics += this->statistics[index];
  }
  return sum_of_statistics;
}
*/
shared_ptr<VentureValue> XRP__DirichletMultinomial_sampler::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 0) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  double random_uniform_0_1 = gsl_ran_flat(random_generator, 0, 1);
  //real sum_of_statistics = this->GetSumOfStatistics();
  double accumulated_probability = 0.0;
  for (size_t index = 0; index < this->statistics.size(); index++) {
    accumulated_probability += this->statistics[index] / sum_of_statistics;
    if (random_uniform_0_1 <= accumulated_probability) {
      return shared_ptr<VentureAtom>(new VentureAtom(index));
    }
  }
  if (fabs(accumulated_probability - 1.0) < comparison_epsilon) {
    return shared_ptr<VentureAtom>(new VentureAtom(this->statistics.size() - 1));
  } else {
    throw std::runtime_error("Strange error in XRP__DirichletMultinomial_sampler.");
  }
}

real XRP__DirichletMultinomial_sampler::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  assert(sampled_value->GetInteger() < this->statistics.size());
  return log(this->statistics[sampled_value->GetInteger()]) - log(this->sum_of_statistics);
}

void XRP__DirichletMultinomial_sampler::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {
  assert(sampled_value->GetInteger() < this->statistics.size());
  this->sum_of_statistics++;
  this->statistics[sampled_value->GetInteger()]++;
}

void XRP__DirichletMultinomial_sampler::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {
  assert(sampled_value->GetInteger() < this->statistics.size());
  this->sum_of_statistics--;
  this->statistics[sampled_value->GetInteger()]--;
  assert(this->statistics[sampled_value->GetInteger()] > 0.0);
}
bool XRP__DirichletMultinomial_sampler::IsRandomChoice() { return true; }
bool XRP__DirichletMultinomial_sampler::CouldBeRescored() { return true; }
string XRP__DirichletMultinomial_sampler::GetName() { return "XRP__DirichletMultinomial_sampler"; }

bool XRP__DirichletMultinomial_sampler::CouldBeEnumerated() {
  return true;
}

set< shared_ptr<VentureValue> > XRP__DirichletMultinomial_sampler::EnumeratingSupport() { // FIXME: pass the *result* by reference, not by value.
  set< shared_ptr<VentureValue> > returning_set;
  for (size_t index = 0; index < this->statistics.size(); index++) {
    returning_set.insert(shared_ptr<VentureAtom>(new VentureAtom(index)));
  }
  return returning_set;
}





shared_ptr<VentureValue> XRP__Set::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  return NIL_INSTANCE;
}
real XRP__Set::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0);
}
void XRP__Set::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {}
void XRP__Set::Remove(vector< shared_ptr<VentureValue> >& arguments,
  shared_ptr<VentureValue> sampled_value) {}
bool XRP__Set::IsRandomChoice() { return false; }
bool XRP__Set::CouldBeRescored() { return false; }
string XRP__Set::GetName() { return "XRP__Set"; }

shared_ptr<VentureValue> XRP__NewSet::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  return shared_ptr<VentureXRP>(new VentureXRP(shared_ptr<XRP>(new XRP__Set())));
}
real XRP__NewSet::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0);
}
void XRP__NewSet::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {}
void XRP__NewSet::Remove(vector< shared_ptr<VentureValue> >& arguments,
  shared_ptr<VentureValue> sampled_value) {}
bool XRP__NewSet::IsRandomChoice() { return false; }
bool XRP__NewSet::CouldBeRescored() { return false; }
string XRP__NewSet::GetName() { return "XRP__NewSet"; }

shared_ptr<VentureValue> XRP__AddToSet::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  return NIL_INSTANCE;
}
real XRP__AddToSet::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0);
}
void XRP__AddToSet::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value)
{
  shared_ptr<XRP__Set> the_set = dynamic_pointer_cast<XRP__Set>(ToVentureType<VentureXRP>(arguments[0])->xrp);
  shared_ptr<VentureValue> element_to_add = arguments[1];
  // assert(the_set->my_set.count(element_to_add) == 0);
  the_set->my_set.insert(element_to_add);
}
void XRP__AddToSet::Remove(vector< shared_ptr<VentureValue> >& arguments,
  shared_ptr<VentureValue> sampled_value)
{
  shared_ptr<XRP__Set> the_set = dynamic_pointer_cast<XRP__Set>(ToVentureType<VentureXRP>(arguments[0])->xrp);
  shared_ptr<VentureValue> element_to_add = arguments[1];
  assert(the_set->my_set.count(element_to_add) > 0);
  the_set->my_set.erase(the_set->my_set.find(element_to_add));
}
bool XRP__AddToSet::IsRandomChoice() { return false; }
bool XRP__AddToSet::CouldBeRescored() { return true; }
string XRP__AddToSet::GetName() { return "XRP__AddToSet"; }

shared_ptr<VentureValue> XRP__SampleFromSet::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  shared_ptr<XRP__Set> the_set = dynamic_pointer_cast<XRP__Set>(ToVentureType<VentureXRP>(arguments[0])->xrp);
  assert(the_set->my_set.size() > 0);
  std::multiset< shared_ptr<VentureValue> >::iterator iterator = the_set->my_set.begin();
  int random_choice_id = UniformDiscrete(0, the_set->my_set.size() - 1);
  std::advance(iterator, random_choice_id);
  return *iterator;
}
real XRP__SampleFromSet::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  shared_ptr<XRP__Set> the_set = dynamic_pointer_cast<XRP__Set>(ToVentureType<VentureXRP>(arguments[0])->xrp);
  return log(1.0 / static_cast<double>(the_set->my_set.size()));
}
void XRP__SampleFromSet::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {}
void XRP__SampleFromSet::Remove(vector< shared_ptr<VentureValue> >& arguments,
  shared_ptr<VentureValue> sampled_value) {}
bool XRP__SampleFromSet::IsRandomChoice() { return true; }
bool XRP__SampleFromSet::CouldBeRescored() { return false; }
string XRP__SampleFromSet::GetName() { return "XRP__SampleFromSet"; }



shared_ptr<VentureValue> XRP__Gensym::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  next_atom_id++;
  return shared_ptr<VentureAtom>(new VentureAtom(next_atom_id));
}

real XRP__Gensym::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                      shared_ptr<VentureValue> sampled_value) {
  return log(1.0);
}

void XRP__Gensym::Incorporate(vector< shared_ptr<VentureValue> >& arguments,
                              shared_ptr<VentureValue> sampled_value) {

}

void XRP__Gensym::Remove(vector< shared_ptr<VentureValue> >& arguments,
                          shared_ptr<VentureValue> sampled_value) {

}
bool XRP__Gensym::IsRandomChoice() { return false; }
bool XRP__Gensym::CouldBeRescored() { return false; }
string XRP__Gensym::GetName() { return "XRP__CRPsampler"; }
