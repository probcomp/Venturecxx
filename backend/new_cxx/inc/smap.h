#ifndef SMAP_H
#define SMAP_H

#include "types.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <iostream>
using std::cout;
using std::endl;

template <typename K,typename V>
struct SamplableMap
{
  map<K, int> d;
  vector<pair<K,V> > a;

  V & get(K k) 
    {       
      assert(size() > 0);
      cout << "get(" << this << ")" << endl; 
      return a[d[k]].second; 
    }
  void set(K k,V v) 
    { 
      cout << "set(" << this << ")" << endl;
      assert(!d.count(k));
      d[k] = a.size();
      a.push_back(make_pair(k,v));
      assert(size() > 0);
    }

  void erase(const K & k) 
    {
      cout << "erase(" << this << ")" << endl;
      assert(d.count(k));
      int index = d[k];
      int lastIndex = a.size() - 1;
      pair<K,V> lastPair = a[lastIndex];

      d[lastPair.first] = index;
      a[index] = lastPair;

      a.pop_back();
      d.erase(k);
      cout << this << ": assert_equal(" << d.size() << "," << a.size() << ")" << endl;
      assert(d.size() == a.size());
    }


  size_t count(const K& k) const { assert(false); }
  size_t size() const { return a.size(); }
  bool contains(K k){ return d.count(k); }

  K & sampleKeyUniformly(gsl_rng * rng) 
    { 
      cout << "sample(" << this << ")" << endl;
      assert(size() > 0);
      int index = gsl_rng_uniform_int(rng, size());
      return a[index].first;
    }

  // TODO for keys(), we should write a custom iterator. 
  // For now, users can just iterate over d and ignore the second element
  
};



#endif
