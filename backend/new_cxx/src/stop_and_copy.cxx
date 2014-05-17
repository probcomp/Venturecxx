#include <boost/foreach.hpp>
#include "concrete_trace.h"

// Deep-copying concrete traces by analogy with the stop-and-copy
// garbage collection algorithm.

shared_ptr<ConcreteTrace> ConcreteTrace::stop_and_copy()
{
  ForwardingMap forward = map<void*, void*>();
  return this->copy_help(forward);
}

template <typename T>
set<T*> copy_set(set<T*> s, ForwardingMap forward)
{
  set<T*> answer = set<T*>();
  BOOST_FOREACH(T* obj, s)
  {
    answer.insert(obj->copy_help(forward));
  }
  return answer;
}

shared_ptr<ConcreteTrace> ConcreteTrace::copy_help(ForwardingMap forward)
{
  shared_ptr<ConcreteTrace> answer = shared_ptr<ConcreteTrace>(new ConcreteTrace);
  answer->globalEnvironment = this->globalEnvironment->copy_help(forward);
  answer->unconstrainedChoices = copy_set(this->unconstrainedChoices, forward);
  answer->constrainedChoices = copy_set(this->constrainedChoices, forward);
  answer->arbitraryErgodicKernels = copy_set(this->arbitraryErgodicKernels, forward);
  answer->unpropagatedObservations = copy_map(this->unpropagatedObservations, forward);
  // ...
  return answer;
}
