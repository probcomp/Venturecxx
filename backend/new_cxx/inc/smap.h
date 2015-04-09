// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#ifndef SMAP_H
#define SMAP_H

#include "types.h"
#include "value.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <iostream>
using std::cout;
using std::endl;

template <typename V>
struct SamplableMap
{
  MapVVPtrInt d;
  vector<pair<VentureValuePtr,V> > a;

  V & get(VentureValuePtr k) 
    {       
      assert(size() > 0);
      assert(d.count(k));
      V & v = a[d[k]].second; 
      return v;
    }
  void set(VentureValuePtr k,V v) 
    { 
      assert(!d.count(k));
      d[k] = a.size();
      a.push_back(make_pair(k,v));
      assert(size() > 0);
    }

  void erase(const VentureValuePtr & k) 
    {
      assert(d.count(k));
      int index = d[k];
      int lastIndex = a.size() - 1;
      pair<VentureValuePtr,V> lastPair = a[lastIndex];

      d[lastPair.first] = index;
      a[index] = lastPair;

      a.pop_back();
      d.erase(k);
      assert(d.size() == a.size());
    }

  // [FIXME] slow and awkward
  // URGENT won't compile because of incomprehensible syntax errors
  vector<VentureValuePtr> getOrderedKeys()
  {
    std::set<VentureValuePtr,VentureValuePtrsLess> keys;
    for (size_t i = 0; i < a.size(); ++i) { keys.insert(a[i].first); }
    vector<VentureValuePtr> orderedKeys(keys.begin(),keys.end());
    return orderedKeys;
  }

  vector<VentureValuePtr> getOrderedKeysInRange(const VentureValuePtr & min, const VentureValuePtr & max)
  {
    std::set<VentureValuePtr,VentureValuePtrsLess> keys;
    for (size_t i = 0; i < a.size(); ++i)
      {
  	if (a[i].first <= max && a[i].first >= min) 
	  { 
	    keys.insert(a[i].first); 
	  }
      }
    return vector<VentureValuePtr>(keys.begin(),keys.end());
  }


  size_t count(const VentureValuePtr& k) const { assert(false); }
  size_t size() const { return a.size(); }
  bool contains(VentureValuePtr k) { return d.count(k); }

  VentureValuePtr & sampleKeyUniformly(gsl_rng * rng) 
    { 
      assert(size() > 0);
      int index = gsl_rng_uniform_int(rng, size());
      return a[index].first;
    }

  // TODO for keys(), we should write a custom iterator. 
  // For now, users can just iterate over d and ignore the second element
  
};

typedef boost::unordered_map<VentureValuePtr, SamplableMap<set<Node*> >, HashVentureValuePtr, VentureValuePtrsEqual> ScopesMap;


#endif
