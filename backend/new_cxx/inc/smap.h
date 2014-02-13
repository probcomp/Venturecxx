#ifndef SMAP_H
#define SMAP_H

#include "types.h"

template <typename K,typename V>
struct SamplableMap
{
  map<K, int> d;
  vector<V> a;

  V& operator[](K k) { assert(false); }
  const V& operator[](K k) const { assert(false); }

  size_t erase(const K & k) { assert(false); }
  size_t count(const K& k) const { assert(false); }
  size_t size() const { assert(false); }

  const K& sampleKeyUniformly() { assert(false); }
  
  // TODO for keys(), we should write a custom iterator. 
  // For now, users can just iterate over d and ignore the second element
  
};



#endif
