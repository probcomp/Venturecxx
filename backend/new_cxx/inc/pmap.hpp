#ifndef PERSISTENT_MAP_H
#define PERSISTENT_MAP_H

#include "wttree.hpp"

#include <iostream>
using std::cout;
using std::endl;

namespace persistent
{
/*
Persistent map backed by a weight-balanced tree.
The lookup method throws an error if the key is not found. Use
the contains method if you aren't sure whether the key exists.
*/
template <typename Key, typename Value, typename Comp = std::less<Key> >
class PMap
{
  typedef typename Node<Key, Value>::NodePtr NodePtr;
  
  NodePtr root;
  Comp comp;
  
  PMap(NodePtr root) : root(root) {} 

public:
  PMap() : root(new Node<Key, Value>()) {}
  
  bool contains(const Key& key)
    { 
      cout << "pmap::contains" << endl;
      return Node<Key, Value>::node_contains(root, key, comp); 
    }
    
  Value lookup(const Key& key)
    { 
      cout << "pmap::lookup" << endl;
      return Node<Key, Value>::node_lookup(root, key, comp); 
    }
  
  PMap insert(const Key& key, const Value& value)
    { 
      cout << "pmap::insert" << endl;
      return PMap(Node<Key, Value>::node_insert(root, key, value, comp)); 
    }
  
  /*
  adjust :: (PMap k v) -> k -> (v -> v) -> PMap k v

  Returns a new PMap obtained from this one by applying the given
  function to the value at the given key. Returns the original PMap
  unchanged if the key is not present. The name is chosen by
  analogy to Data.PMap.adjust from the Haskell standard library.
  */
  template <class Function>
  PMap adjust(const Key& key, const Function& f)
    { return PMap(Node<Key, Value>::node_adjust(root, key, f, comp)); }
  
  PMap remove(const Key& key)
    { return PMap(Node<Key, Value>::node_remove(root, key, comp)); }

  size_t size() { return root->size; }
  
  vector<Key> keys()
    { return Node<Key, Value>::node_traverse_keys_in_order(root); }
  
  vector<pair<Key, Value> > items()
    { return Node<Key, Value>::node_traverse_items_in_order(root); }  
};

};
#endif
