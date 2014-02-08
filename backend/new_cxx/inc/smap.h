#ifndef SMAP_H
#define SMAP_H

#include <map>
#include <vector>

using std::map;
using std::vector;
using std::size_type;

struct SamplableMap<K,V>
{
  map<K, int> d;
  vector<V> a;

  V& operator[](K k);
  const V& operator[](K k) const;

  size_type erase(const K & k);
  size_type count(const K& k) const;
  size_type size() const;

  const K& sampleKeyUniformly();
  
  // TODO for keys(), we should write a custom iterator. 
  // For now, users can just iterate over d and ignore the second element
  
};



#endif
