#include <boost/foreach.hpp>
#include "concrete_trace.h"
#include "env.h"
#include "sps/csp.h"
#include "sps/msp.h"
#include "pytrace.h"
#include "stop-and-copy.h"

// Deep-copying concrete traces by analogy with the stop-and-copy
// garbage collection algorithm.

// This implementation relies on all reachable Venture objects
// correctly implementing a copy_help method of type
//
//   Foo* Foo::copy_help(ForwardingMap* forward)
//
// The contract is that copy_help must copy the object it is called
// on, translating all Venture objects inside according to the given
// forwarding map, and insert a forwarding pointer from this to the
// result.  The caller owns both the ForwardingMap* and the returned
// Foo*.
//
// A typical implementation looks like
//
//   Foo* answer = new Foo(this);
//   (*forward)[this] = answer;
//   ... // copy fields
//   return answer;
//
// Note that the forwarding map needs to be mutated before recursively
// copying the fields, to break reference cycles.  This file contains
// copy_help implementations for almost all current Venture objects,
// as well as a bunch of utilities for copying various standard types
// (like sets, shared_pointers, etc).  Use copy_pointer to copy raw
// pointers rather than calling their copy_help methods directly,
// because copy_pointer encapsulates the cycle-breaking at the heart
// of the algorithm (and calls the object's copy_help method only if
// needed).

size_t ForwardingMap::count(const void* k) const
{
  return pointers.count(k);
}

void*& ForwardingMap::operator[] (const void* k)
{
  return pointers[k];
}

PyTrace* PyTrace::stop_and_copy() const
{
  PyTrace* answer = new PyTrace(*this);
  answer->trace = this->trace->stop_and_copy();
  return answer;
}

shared_ptr<ConcreteTrace> ConcreteTrace::stop_and_copy() const
{
  ForwardingMap forward = ForwardingMap();
  return this->copy_help(&forward);
}

/*********************************************************************\
|* Generic                                                           *|
\*********************************************************************/

template <typename T>
T* copy_pointer(const T* v, ForwardingMap* forward)
{
  if (v == NULL)
  {
    return NULL;
  }
  if (forward->count(v) > 0)
  {
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
shared_ptr<T> copy_shared(const shared_ptr<T>& v, ForwardingMap* forward)
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
set<T*> copy_set(const set<T*>& s, ForwardingMap* forward)
{
  set<T*> answer = set<T*>();
  BOOST_FOREACH(T* obj, s)
  {
    answer.insert(copy_pointer(obj, forward));
  }
  return answer;
}

template <typename T>
set<shared_ptr<T> > copy_set_shared(const set<shared_ptr<T> >& s, ForwardingMap* forward)
{
  set<shared_ptr<T> > answer = set<shared_ptr<T> >();
  BOOST_FOREACH(shared_ptr<T> obj, s)
  {
    answer.insert(copy_shared(obj, forward));
  }
  return answer;
}

template <typename K, typename V>
map<K*, V> copy_map_k(const map<K*, V>& m, ForwardingMap* forward)
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
map<shared_ptr<K>, V> copy_map_shared_k(const map<shared_ptr<K>, V>& m, ForwardingMap* forward)
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
map<K, V*> copy_map_v(const map<K, V*>& m, ForwardingMap* forward)
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
map<K, shared_ptr<V> > copy_map_shared_v(const map<K, shared_ptr<V> >& m, ForwardingMap* forward)
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
map<K*, shared_ptr<V> > copy_map_kv(const map<K*, shared_ptr<V> >& m, ForwardingMap* forward)
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
BlocksMap copy_blocks_map(const BlocksMap& m, ForwardingMap* forward)
{
  BlocksMap answer = BlocksMap();
  for(typename vector<pair<VentureValuePtr,set<Node*> > >::const_iterator itr = m.a.begin();
      itr != m.a.end(); ++itr)
  {
    answer.a.push_back( pair<VentureValuePtr,set<Node*> >(copy_shared((*itr).first, forward),
                                                          copy_set((*itr).second, forward)));
  }
  for(typename MapVVPtrInt::const_iterator itr = m.d.begin();
      itr != m.d.end(); ++itr)
  {
    answer.d[copy_shared((*itr).first, forward)] = (*itr).second;
  }
  return answer;
}

ScopesMap copy_scopes_map(const ScopesMap& m, ForwardingMap* forward)
{
  ScopesMap answer = ScopesMap();
  typename ScopesMap::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    SamplableMap<std::set<Node*> > explictly_typed = copy_blocks_map((*itr).second, forward);
    answer[copy_shared((*itr).first, forward)] = explictly_typed;
  }
  return answer;
}

template <typename V>
boost::unordered_map<VentureValuePtr, V, HashVentureValuePtr, VentureValuePtrsEqual> copy_vvptr_map_shared_v(const boost::unordered_map<VentureValuePtr, V, HashVentureValuePtr, VentureValuePtrsEqual>& m, ForwardingMap* forward)
{
  boost::unordered_map<VentureValuePtr, V, HashVentureValuePtr, VentureValuePtrsEqual> answer = boost::unordered_map<VentureValuePtr, V, HashVentureValuePtr, VentureValuePtrsEqual>();
  typename boost::unordered_map<VentureValuePtr, V, HashVentureValuePtr, VentureValuePtrsEqual>::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    answer[copy_shared((*itr).first, forward)] = copy_shared((*itr).second, forward);
  }
  return answer;
}

template <typename V>
vector<V*> copy_vector(const vector<V*>& v, ForwardingMap* forward)
{
  vector<V*> answer = vector<V*>();
  BOOST_FOREACH(V* val, v)
    {
      answer.push_back(copy_pointer(val, forward));
    }
  return answer;
}

template <typename V>
vector<shared_ptr<V> > copy_vector_shared(const vector<shared_ptr<V> >& v, ForwardingMap* forward)
{
  vector<shared_ptr<V> > answer = vector<shared_ptr<V> >();
  BOOST_FOREACH(shared_ptr<V> val, v)
    {
      answer.push_back(copy_shared(val, forward));
    }
  return answer;
}

template <typename K, typename V>
map<K*, vector<shared_ptr<V> > > copy_map_k_vectorv(const map<K*, vector<shared_ptr<V> > >& m, ForwardingMap* forward)
{
  map<K*, vector<shared_ptr<V> > > answer = map<K*, vector<shared_ptr<V> > >();
  typename map<K*, vector<shared_ptr<V> > >::const_iterator itr;
  for(itr = m.begin(); itr != m.end(); ++itr)
  {
    if (!((*itr).second.empty()))
    { // Avoid inserting empty entries; their keys may be stale, and
      // they get auto-generated if needed.
      answer[copy_pointer((*itr).first, forward)] = copy_vector_shared((*itr).second, forward);
    }
  }
  return answer;
}

/*********************************************************************\
|* Concrete Traces                                                   *|
\*********************************************************************/

shared_ptr<ConcreteTrace> ConcreteTrace::copy_help(ForwardingMap* forward) const
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
  answer->seekInconsistencies();
  return answer;
}

/*********************************************************************\
|* Nodes                                                             *|
\*********************************************************************/

// The following looks ripe for some macrology (especially the if),
// but I don't want to go there.
ConstantNode* ConstantNode::copy_help(ForwardingMap* forward) const
{
  ConstantNode* answer = new ConstantNode(this->exp);
  (*forward)[this] = answer;
  answer->exp = copy_shared(this->exp, forward);
  answer->children = copy_set(this->children, forward);
  return answer;
}

LookupNode* LookupNode::copy_help(ForwardingMap* forward) const
{
  LookupNode* answer = new LookupNode(*this);
  (*forward)[this] = answer;
  answer->exp = copy_shared(this->exp, forward);
  answer->sourceNode = copy_pointer(this->sourceNode, forward);
  answer->children = copy_set(this->children, forward);
  return answer;
}

RequestNode* RequestNode::copy_help(ForwardingMap* forward) const
{
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

OutputNode* OutputNode::copy_help(ForwardingMap* forward) const
{
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

/*********************************************************************\
|* SP Things                                                         *|
\*********************************************************************/

SP* SP::copy_help(ForwardingMap* forward) const
{
  SP* answer = new SP(*this);
  (*forward)[this] = answer;
  answer->requestPSP = copy_shared(this->requestPSP, forward);
  answer->outputPSP = copy_shared(this->outputPSP, forward);
  return answer;
}

VentureSPRef* VentureSPRef::copy_help(ForwardingMap* forward) const
{
  VentureSPRef* answer = new VentureSPRef(*this);
  (*forward)[this] = answer;
  answer->makerNode = copy_pointer(this->makerNode, forward);
  return answer;
}

VentureSPRecord* VentureSPRecord::copy_help(ForwardingMap* forward) const
{
  VentureSPRecord* answer = new VentureSPRecord(*this);
  (*forward)[this] = answer;
  answer->sp = copy_shared(this->sp, forward);
  answer->spAux = copy_shared(this->spAux, forward);
  answer->spFamilies = copy_shared(this->spFamilies, forward);
  return answer;
}

SPFamilies* SPFamilies::copy_help(ForwardingMap* forward) const
{
  SPFamilies* answer = new SPFamilies(*this);
  (*forward)[this] = answer;
  answer->families = copy_vvptr_map_shared_v(this->families, forward);
  return answer;
}

CSPRequestPSP* CSPRequestPSP::copy_help(ForwardingMap* forward) const
{
  CSPRequestPSP* answer = new CSPRequestPSP(*this);
  (*forward)[this] = answer;
  answer->expression = copy_shared(this->expression, forward);
  answer->environment = copy_shared(this->environment, forward);
  return answer;
}

MSPRequestPSP* MSPRequestPSP::copy_help(ForwardingMap* forward) const
{
  MSPRequestPSP* answer = new MSPRequestPSP(*this);
  (*forward)[this] = answer;
  answer->sharedOperatorNode = copy_pointer(this->sharedOperatorNode, forward);
  return answer;
}

/*********************************************************************\
|* Values                                                            *|
\*********************************************************************/

VentureEnvironment* VentureEnvironment::copy_help(ForwardingMap* forward) const
{
  VentureEnvironment* answer = new VentureEnvironment(*this);
  (*forward)[this] = answer;
  answer->outerEnv = copy_shared(this->outerEnv, forward);
  answer->frame = copy_map_v(this->frame, forward);
  return answer;
}

VentureArray* VentureArray::copy_help(ForwardingMap* forward) const
{
  VentureArray* answer = new VentureArray(*this);
  (*forward)[this] = answer;
  answer->xs = copy_vector_shared(this->xs, forward);
  return answer;
}

VenturePair* VenturePair::copy_help(ForwardingMap* forward) const
{
  VenturePair* answer = new VenturePair(*this);
  (*forward)[this] = answer;
  answer->car = copy_shared(this->car, forward);
  answer->cdr = copy_shared(this->cdr, forward);
  return answer;
}

VentureDictionary* VentureDictionary::copy_help(ForwardingMap* forward) const
{
  VentureDictionary* answer = new VentureDictionary(*this);
  (*forward)[this] = answer;
  answer->dict = copy_vvptr_map_shared_v(this->dict, forward);
  return answer;
}

VentureNode* VentureNode::copy_help(ForwardingMap* forward) const
{
  VentureNode* answer = new VentureNode(*this);
  (*forward)[this] = answer;
  answer->node = copy_pointer(this->node, forward);
  return answer;
}
