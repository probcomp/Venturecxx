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

#ifndef PERSISTENT_SET_H
#define PERSISTENT_SET_H

#include "wttree.hpp"

namespace persistent
{
/*
Persistent set backed by a weight-balanced tree.
At present, happens to be implemented just like a PMap, but with the
values always being True. In principle could be impemented more
efficiently by specializing the nodes not to store values at all.
*/
template <typename Key, typename Comp = std::less<Key> >
class PSet
{
  typedef typename Node<Key, bool>::NodePtr NodePtr;
  
  NodePtr root;
  Comp comp;
  
  PSet(NodePtr root) : root(root) {} 

public:
  PSet() : root(new Node<Key, bool>()) {}

  
  bool contains(const Key& key)
    { 
      //      cout << "pset::contains" << endl;
      return Node<Key, bool>::node_contains(root, key, comp); 
    }
  
  PSet insert(const Key& key)
    { 
      //      cout << "pset::contains" << endl;
      return PSet(Node<Key, bool>::node_insert(root, key, true, comp)); 
    }
  
  /*
  adjust :: (PSet k v) -> k -> (v -> v) -> PSet k v

  Returns a new PSet obtained from this one by applying the given
  function to the bool at the given key. Returns the original PSet
  unchanged if the key is not present. The name is chosen by
  analogy to Data.PSet.adjust from the Haskell standard library.
  */
  template <class Function>
  PSet adjust(const Key& key, const Function& f)
    { return PSet(Node<Key, bool>::node_adjust(root, key, f, comp)); }
  
  PSet remove(const Key& key)
    { return PSet(Node<Key, bool>::node_remove(root, key, comp)); }

  size_t size() { return root->size; }
  
  vector<Key> keys()
    { return Node<Key, bool>::node_traverse_keys_in_order(root); }
};
};
/*
TODO test balance, either as asymptotics with the timings framework
or through an explicit check that a tree built by some mechanism is
balanced->  Issue https://app->asana->com/0/9277419963067/9924589720809
*/

#endif
