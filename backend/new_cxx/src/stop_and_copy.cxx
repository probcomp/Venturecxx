#include <boost/foreach.hpp>
#include "concrete_trace.h"
#include "env.h"

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

template <typename K, typename V>
map<K*, V> copy_map_k(map<K*, V> m, ForwardingMap forward)
{
  map<K*, V> answer = map<K*, V>();
  typename map<K*, V>::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[(*itr).first->copy_help(forward)] = (*itr).second;
  }
  return answer;
}

template <typename K, typename V>
map<K*, shared_ptr<V> > copy_map_kv(map<K*, shared_ptr<V> > m, ForwardingMap forward)
{
  map<K*, shared_ptr<V> > answer = map<K*, shared_ptr<V> >();
  typename map<K*, shared_ptr<V> >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[(*itr).first->copy_help(forward)] = (*itr).second->copy_help(forward);
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
  answer->unpropagatedObservations = copy_map_k(this->unpropagatedObservations, forward);
  answer->aaaMadeSPAuxs = copy_map_kv(this->aaaMadeSPAuxs, forward);
  // ...
  return answer;
}
