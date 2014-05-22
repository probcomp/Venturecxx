#include <boost/foreach.hpp>
#include "concrete_trace.h"
#include "env.h"
#include "sps/csp.h"
#include "sps/msp.h"
#include "pytrace.h"
#include "stop-and-copy.h"

// Deep-copying concrete traces by analogy with the stop-and-copy
// garbage collection algorithm.

size_t ForwardingMap::count(void* k) const
{
  return pointers.count(k);
}

void*& ForwardingMap::operator[] (void* k)
{
  return pointers[k];
}

PyTrace* PyTrace::stop_and_copy()
{
  assert(!this->continuous_inference_running);
  assert(!this->continuous_inference_thread);
  PyTrace* answer = new PyTrace(*this);
  answer->trace = this->trace->stop_and_copy();
  return answer;
}

shared_ptr<ConcreteTrace> ConcreteTrace::stop_and_copy()
{
  ForwardingMap forward = ForwardingMap();
  return this->copy_help(&forward);
}

/*********************************************************************\
|* Generic                                                           *|
\*********************************************************************/

template <typename T>
T* copy_pointer(T* v, ForwardingMap* forward)
{
  if (forward->count(v) > 0) {
    return (T*)(*forward)[v];
  } else {
    T* answer = dynamic_cast<T*>(v->copy_help(forward));
    assert(answer);
    if (answer != v)
    { // Should put an appropriate forwarding pointer in the
      // forwarding map.
      assert(forward->count(v) > 0);
      assert(answer == (*forward)[v]);
    } // Otherwise no copying was needed
    return answer;
  }
}

template <typename T>
shared_ptr<T> copy_shared(shared_ptr<T> v, ForwardingMap* forward)
{
  if (v.get() == 0)
  {
    return v;
  }
  else if (forward->shared_ptrs.count(v.get()) > 0)
  {
    // Make sure that any given raw pointer gets at most one shared
    // pointer made out of it
    return static_pointer_cast<T> (forward->shared_ptrs[v.get()]);
  }
  else if (forward->count(v.get()) > 0)
  {
    shared_ptr<T> answer = shared_ptr<T>( (T*)(*forward)[v.get()] );
    forward->shared_ptrs[v.get()] = answer;
    return answer;
  } else {
    T* result = copy_pointer(v.get(), forward);
    if (result == v.get())
    {
      // No copying was needed
      return v;
    } else {
      // The forwarding map was mutated by copying the underlying object
      // so try again, this time finding the raw pointer in the map.
      assert(forward->count(v.get()) > 0);
      return copy_shared(v, forward);
    }
  }
}

template <typename T>
set<T*> copy_set(set<T*> s, ForwardingMap* forward)
{
  set<T*> answer = set<T*>();
  BOOST_FOREACH(T* obj, s)
  {
    answer.insert(copy_pointer(obj, forward));
  }
  return answer;
}

template <typename T>
set<shared_ptr<T> > copy_set_shared(set<shared_ptr<T> > s, ForwardingMap* forward)
{
  set<shared_ptr<T> > answer = set<shared_ptr<T> >();
  BOOST_FOREACH(shared_ptr<T> obj, s)
  {
    answer.insert(copy_shared(obj, forward));
  }
  return answer;
}

template <typename K, typename V>
map<K*, V> copy_map_k(map<K*, V> m, ForwardingMap* forward)
{
  map<K*, V> answer = map<K*, V>();
  typename map<K*, V>::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_pointer((*itr).first, forward)] = (*itr).second;
  }
  return answer;
}

template <typename K, typename V>
map<shared_ptr<K>, V> copy_map_shared_k(map<shared_ptr<K>, V> m, ForwardingMap* forward)
{
  map<shared_ptr<K>, V> answer = map<shared_ptr<K>, V>();
  typename map<shared_ptr<K>, V>::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_shared((*itr).first, forward)] = (*itr).second;
  }
  return answer;
}

template <typename K, typename V>
map<K, V*> copy_map_v(map<K, V*> m, ForwardingMap* forward)
{
  map<K, V*> answer = map<K, V*>();
  typename map<K, V*>::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[(*itr).first] = copy_pointer((*itr).second, forward);
  }
  return answer;
}

template <typename K, typename V>
map<K, shared_ptr<V> > copy_map_shared_v(map<K, shared_ptr<V> > m, ForwardingMap* forward)
{
  map<K, shared_ptr<V> > answer = map<K, shared_ptr<V> >();
  typename map<K, shared_ptr<V> >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[(*itr).first] = copy_shared((*itr).second, forward);
  }
  return answer;
}

template <typename K, typename V>
map<K*, shared_ptr<V> > copy_map_kv(map<K*, shared_ptr<V> > m, ForwardingMap* forward)
{
  map<K*, shared_ptr<V> > answer = map<K*, shared_ptr<V> >();
  typename map<K*, shared_ptr<V> >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_pointer((*itr).first, forward)] = copy_shared((*itr).second, forward);
  }
  return answer;
}

typedef SamplableMap<set<Node*> > BlocksMap;
BlocksMap copy_blocks_map(BlocksMap m, ForwardingMap* forward)
{
  BlocksMap answer = BlocksMap();
  for(typename vector<pair<VentureValuePtr,set<Node*> > >::const_iterator itr = m.a.begin();
      itr != m.a.end(); ++itr)
  {
    answer.a.push_back( pair<VentureValuePtr,set<Node*> >((*itr).first,
                                                          copy_set((*itr).second, forward)));
  }
  for(typename VentureValuePtrMap<int>::const_iterator itr = m.d.begin();
      itr != m.d.end(); ++itr)
  {
    answer.d[(*itr).first] = (*itr).second;
  }
  return answer;
}

typedef VentureValuePtrMap<SamplableMap<set<Node*> > > ScopesMap;
ScopesMap copy_scopes_map(ScopesMap m, ForwardingMap* forward)
{
  ScopesMap answer = ScopesMap();
  typename ScopesMap::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_shared((*itr).first, forward)] = copy_blocks_map((*itr).second, forward);
  }
  return answer;
}

template <typename V>
VentureValuePtrMap<shared_ptr<V> > copy_vvptr_map_shared_v(VentureValuePtrMap<shared_ptr<V> > m, ForwardingMap* forward)
{
  VentureValuePtrMap<shared_ptr<V> > answer = VentureValuePtrMap<shared_ptr<V> >();
  typename VentureValuePtrMap<shared_ptr<V> >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_shared((*itr).first, forward)] = copy_shared((*itr).second, forward);
  }
  return answer;
}

template <typename V>
vector<V*> copy_vector(vector<V*> v, ForwardingMap* forward)
{
  vector<V*> answer = vector<V*>();
  BOOST_FOREACH(V* val, v)
    {
      answer.push_back(copy_pointer(val, forward));
    }
  return answer;
}

template <typename V>
vector<shared_ptr<V> > copy_vector_shared(vector<shared_ptr<V> > v, ForwardingMap* forward)
{
  vector<shared_ptr<V> > answer = vector<shared_ptr<V> >();
  BOOST_FOREACH(shared_ptr<V> val, v)
    {
      answer.push_back(copy_shared(val, forward));
    }
  return answer;
}

template <typename K, typename V>
map<K*, vector<shared_ptr<V> > > copy_map_k_vectorv(map<K*, vector<shared_ptr<V> > > m, ForwardingMap* forward)
{
  map<K*, vector<shared_ptr<V> > > answer = map<K*, vector<shared_ptr<V> > >();
  typename map<K*, vector<shared_ptr<V> > >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_pointer((*itr).first, forward)] = copy_vector_shared((*itr).second, forward);
  }
  return answer;
}

/*********************************************************************\
|* Concrete Traces                                                   *|
\*********************************************************************/

shared_ptr<ConcreteTrace> ConcreteTrace::copy_help(ForwardingMap* forward)
{
  shared_ptr<ConcreteTrace> answer = shared_ptr<ConcreteTrace>(new ConcreteTrace);
  answer->globalEnvironment = copy_shared(this->globalEnvironment, forward);
  answer->unconstrainedChoices = copy_set(this->unconstrainedChoices, forward);
  answer->constrainedChoices = copy_set(this->constrainedChoices, forward);
  answer->arbitraryErgodicKernels = copy_set(this->arbitraryErgodicKernels, forward);
  answer->unpropagatedObservations = copy_map_kv(this->unpropagatedObservations, forward);
  answer->aaaMadeSPAuxs = copy_map_kv(this->aaaMadeSPAuxs, forward);
  answer->families = copy_map_shared_v(this->families, forward);
  answer->scopes = copy_scopes_map(this->scopes, forward);
  answer->esrRoots = copy_map_k_vectorv(this->esrRoots, forward);
  answer->numRequests = copy_map_shared_k(this->numRequests, forward);
  answer->madeSPRecords = copy_map_kv(this->madeSPRecords, forward);
  answer->values = copy_map_kv(this->values, forward);
  answer->observedValues = copy_map_kv(this->observedValues, forward);
  answer->builtInNodes = copy_set_shared(this->builtInNodes, forward);
  return answer;
}

/*********************************************************************\
|* Nodes                                                             *|
\*********************************************************************/

// The following looks ripe for some macrology (especially the if),
// but I don't want to go there.
ConstantNode* ConstantNode::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (ConstantNode*)(*forward)[this];
  } else {
    ConstantNode* answer = new ConstantNode(this->exp);
    (*forward)[this] = answer;
    answer->exp = copy_shared(this->exp, forward);
    answer->children = copy_set(this->children, forward);
    return answer;
  }
}

LookupNode* LookupNode::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (LookupNode*)(*forward)[this];
  } else {
    LookupNode* answer = new LookupNode(*this);
    (*forward)[this] = answer;
    answer->exp = copy_shared(this->exp, forward);
    answer->sourceNode = copy_pointer(this->sourceNode, forward);
    answer->children = copy_set(this->children, forward);
    return answer;
  }
}

RequestNode* RequestNode::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (RequestNode*)(*forward)[this];
  } else {
    RequestNode* answer = new RequestNode(*this);
    (*forward)[this] = answer;
    answer->exp = copy_shared(this->exp, forward);
    answer->outputNode = copy_pointer(this->outputNode, forward);
    answer->operatorNode = copy_pointer(this->operatorNode, forward);
    answer->operandNodes = copy_vector(this->operandNodes, forward);
    answer->env = copy_shared(this->env, forward);
    answer->children = copy_set(this->children, forward);
    return answer;
  }
}

OutputNode* OutputNode::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (OutputNode*)(*forward)[this];
  } else {
    OutputNode* answer = new OutputNode(*this);
    (*forward)[this] = answer;
    answer->exp = copy_shared(this->exp, forward);
    answer->requestNode = copy_pointer(this->requestNode, forward);
    answer->operatorNode = copy_pointer(this->operatorNode, forward);
    answer->operandNodes = copy_vector(this->operandNodes, forward);
    answer->env = copy_shared(this->env, forward);
    answer->children = copy_set(this->children, forward);
    return answer;
  }
}

/*********************************************************************\
|* SP Things                                                         *|
\*********************************************************************/

SP* SP::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (SP*)(*forward)[this];
  } else {
    SP* answer = new SP(*this);
    (*forward)[this] = answer;
    answer->requestPSP = copy_shared(this->requestPSP, forward);
    answer->outputPSP = copy_shared(this->outputPSP, forward);
    return answer;
  }
}

VentureSPRef* VentureSPRef::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (VentureSPRef*)(*forward)[this];
  } else {
    VentureSPRef* answer = new VentureSPRef(*this);
    (*forward)[this] = answer;
    answer->makerNode = copy_pointer(this->makerNode, forward);
    return answer;
  }
}

VentureSPRecord* VentureSPRecord::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (VentureSPRecord*)(*forward)[this];
  } else {
    VentureSPRecord* answer = new VentureSPRecord(*this);
    (*forward)[this] = answer;
    answer->sp = copy_shared(this->sp, forward);
    answer->spAux = copy_shared(this->spAux, forward);
    answer->spFamilies = copy_shared(this->spFamilies, forward);
    return answer;
  }
}

SPFamilies* SPFamilies::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (SPFamilies*)(*forward)[this];
  } else {
    SPFamilies* answer = new SPFamilies(*this);
    (*forward)[this] = answer;
    answer->families = copy_vvptr_map_shared_v(this->families, forward);
    return answer;
  }
}

CSPRequestPSP* CSPRequestPSP::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (CSPRequestPSP*)(*forward)[this];
  } else {
    CSPRequestPSP* answer = new CSPRequestPSP(*this);
    (*forward)[this] = answer;
    answer->expression = copy_shared(this->expression, forward);
    answer->environment = copy_shared(this->environment, forward);
    return answer;
  }
}

MSPRequestPSP* MSPRequestPSP::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (MSPRequestPSP*)(*forward)[this];
  } else {
    MSPRequestPSP* answer = new MSPRequestPSP(*this);
    (*forward)[this] = answer;
    answer->sharedOperatorNode = copy_pointer(this->sharedOperatorNode, forward);
    return answer;
  }
}

/*********************************************************************\
|* Environments                                                      *|
\*********************************************************************/

VentureEnvironment* VentureEnvironment::copy_help(ForwardingMap* forward)
{
  if (forward->count(this) > 0)
  {
    return (VentureEnvironment*)(*forward)[this];
  } else {
    VentureEnvironment* answer = new VentureEnvironment(*this);
    (*forward)[this] = answer;
    answer->outerEnv = copy_shared(this->outerEnv, forward);
    answer->frame = copy_map_v(this->frame, forward);
    return answer;
  }
}
