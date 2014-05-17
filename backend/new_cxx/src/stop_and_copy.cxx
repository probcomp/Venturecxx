#include "concrete_trace.h"

shared_ptr<ConcreteTrace> ConcreteTrace::stop_and_copy()
{
  ForwardingMap forward = map<void*, void*>();
  return this->copy_help(forward);
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
  return answer
}

