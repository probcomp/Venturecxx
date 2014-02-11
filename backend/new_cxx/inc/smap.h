#ifndef SMAP_H
#define SMAP_H

#include "types.h"

template <typename K,typename V>
struct SamplableMap
{
  map<K, int> d;
  vector<V> a;

  V& operator[](K k) { throw 500; }
  const V& operator[](K k) const { throw 500; }

  size_t erase(const K & k) { throw 500; }
  size_t count(const K& k) const { throw 500; }
  size_t size() const { throw 500; }

  const K& sampleKeyUniformly() { throw 500; }
  
  // TODO for keys(), we should write a custom iterator. 
  // For now, users can just iterate over d and ignore the second element
  
};



#endif
