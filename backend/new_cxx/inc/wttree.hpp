#ifndef PMAP_H
#define PMAP_H

/*
Weight-balanced trees.

This program is based on

  Stephen Adams, Implementing Sets Efficiently in a Functional
     Language, CSTR 92-10, Department of Electronics and Computer
     Science, University of Southampton, 1992.

but only implements the operations that are useful for Venture.
The actual implementation is cribbed close to verbatim from wt-trees
in MIT Scheme, which were written by Stephen Adams and modified by
Chris Hansen and Taylor Campbell.
*/

// Style note: all node keys and subtrees are always listed in function
// arguments in-order.

#include <vector>
#include <utility>
#include <boost/shared_ptr.hpp>
#include <boost/tuple/tuple.hpp>

namespace wttree
{

using std::vector;
using std::pair;
using boost::tuples::tuple;
using boost::tuples::get;

template <typename Key, typename Value>
struct Node
{
  typedef boost::shared_ptr<const Node> NodePtr;

  Node() : size(0) {}

  Node(const NodePtr& left, const Key& key, const Value& value, const NodePtr& right) :
    left(left), key(key), value(value), right(right),
    size(left->size + right->size + 1)
  {}
  
  bool isEmpty() const { return size == 0; }
  
  NodePtr left, right;
  size_t size;
  Key key;
  Value value;
  
  static int node_weight(const NodePtr& node)
  {
    return node->size + 1;
  }

  static NodePtr single_left(const NodePtr& x, const Key& akey, const Value& avalue, const NodePtr& r)
  {
    return NodePtr(new Node(NodePtr(new Node(x, akey, avalue, r->left)), r->key, r->value, r->right));
  }

  static NodePtr single_right(const NodePtr& l, const Key& bkey, const Value& bvalue, const NodePtr& z)
  {
    return NodePtr(new Node(l->left, l->key, l->value, NodePtr(new Node(l->right, bkey, bvalue, z))));
  }

  static NodePtr double_left(const NodePtr& x, const Key& akey, const Value& avalue, const NodePtr& r)
  {
    return NodePtr(new Node(
                NodePtr(new Node(x, akey, avalue, r->left->left)),
                r->left->key, r->left->value,
                NodePtr(new Node(r->left->right, r->key, r->value, r->right))
                ));
  }
  
  static NodePtr double_right(const NodePtr& l, const Key& ckey, const Value& cvalue, const NodePtr& z)
  {
    return NodePtr(new Node(
                NodePtr(new Node(l->left, l->key, l->value, l->right->left)),
                l->right->key, l->right->value,
                NodePtr(new Node(l->right->right, ckey, cvalue, z))
                ));
  }
  
  /*
  For the provenance of these constants, see Yoichi Hirai and Kazuhiko
  Yamamoto, `Balancing Weight-Balanced Trees', Journal of Functional
  Programming 21(3), 2011.
  */

  static const int _DELTA = 3;
  static const int _GAMMA = 2;

  static NodePtr t_join(const NodePtr& l, const Key& key, const Value& value, const NodePtr& r)
  {
    int l_w = node_weight(l);
    int r_w = node_weight(r);
    if (r_w > _DELTA * l_w)
    {
      // Right is too big
      if (node_weight(r->left) < _GAMMA * node_weight(r->right))
      {
        return single_left(l, key, value, r);
      }
      else
      {
        return double_left(l, key, value, r);
      }
    }
    else if (l_w > _DELTA * r_w)
    {
      // Left is too big
      if (node_weight(l->right) < _GAMMA * node_weight(l->left))
      {
        return single_right(l, key, value, r);
      }
      else
      {
        return double_right(l, key, value, r);
      }
    }
    else
    {
      return NodePtr(new Node(l, key, value, r));
    }
  }

  static tuple<Key, Value, NodePtr> node_popmin(const NodePtr& node)
  {
    if (node->isEmpty())
    {
      assert(false);
      throw "Trying to pop the minimum off an empty node";
    }
    else if (node->left->isEmpty())
    {
      return tuple<Key, Value, NodePtr>(node->key, node->value, node->right);
    }
    else
    {
      // TODO Is this constant creation and destruction of tuples
      // actually any more efficient than just finding the minimum in one
      // pass and removing it in another?
      tuple<Key, Value, NodePtr> min = node_popmin(node->left);
      return tuple<Key, Value, NodePtr>(get<0>(min), get<1>(min), t_join(get<2>(min), node->key, node->value, node->right));
    }
  }

  static bool node_contains(const NodePtr& node, const Key& key)
  {
    if (node->isEmpty())
    {
      return false;
    }
    else if (key < node->key)
    {
      return node_contains(node->left, key);
    }
    else if (node->key < key)
    {
      return node_contains(node->right, key);
    }
    else
    {
      return true;
    }
  }

  static Value node_lookup(const NodePtr& node, const Key& key)
  {
    if (node->isEmpty())
    {
      assert(false);
      throw "Key does not exist.";
    }
    else if (key < node->key)
    {
      return node_lookup(node->left, key);
    }
    else if (node->key < key)
    {
      return node_lookup(node->right, key);
    }
    else
    {
      return node->value;
    }
  }

  static NodePtr node_insert(const NodePtr& node, const Key& key, const Value& value)
  {
    if (node->isEmpty())
    {
      return NodePtr(new Node(NodePtr(new Node()), key, value, NodePtr(new Node())));
    }
    else if (key < node->key)
    {
      return t_join(node_insert(node->left, key, value),
                    node->key, node->value, node->right);
    }
    else if (node->key < key)
    {
      return t_join(node->left, node->key, node->value,
                    node_insert(node->right, key, value));
    }
    else
    {
      return NodePtr(new Node(node->left, key, value, node->right));
    }
  }

  template <class Function>
  static NodePtr node_adjust(const NodePtr& node, const Key& key, const Function& f)
  {
    if (node->isEmpty())
    {
      // TODO Optimize the not-found case by not reconstructing the tree
      // on the way up?
      return node;
    }
    else if (key < node->key)
    {
      return NodePtr(new Node(node_adjust(node->left, key, f),
                  node->key, node->value, node->right));
    }
    else if (node->key < key)
    {
      return NodePtr(new Node(node->left, node->key, node->value,
                  node_adjust(node->right, key, f)));
    }
    else
    {
      return NodePtr(new Node(node->left, key, f(node->value), node->right));
    }
  }

  static NodePtr node_remove(const NodePtr& node, const Key& key)
  {
    if (node->isEmpty())
    {
      return node;
    }
    else if (key < node->key)
    {
      return t_join(node_remove(node->left, key),
                    node->key, node->value, node->right);
    }
    else if (node->key < key)
    {
      return t_join(node->left, node->key, node->value,
                    node_remove(node->right, key));
    }
    else
    {
      // Deleting the key at this node
      if (node->right->isEmpty())
      {
        return node->left;
      }
      else if (node->left->isEmpty())
      {
        return node->right;
      }
      else
      {
        tuple<Key, Value, NodePtr> min = node_popmin(node->right);
        return t_join(node->left, get<0>(min), get<1>(min), get<2>(min));
      }
    }
  }

  // impure helper function
  static void node_traverse_in_order(const NodePtr& node, vector<NodePtr>& nodes)
  {
    if (!node->isEmpty())
    {
      node_traverse_in_order(node->left, nodes);
      nodes.push_back(node);
      node_traverse_in_order(node->right, nodes);
    }
  }

  static vector<Key> node_traverse_keys_in_order(const NodePtr& node)
  {
    vector<NodePtr> nodes;
    nodes.reserve(node->size);
    node_traverse_in_order(node, nodes);
    
    vector<Key> keys;
    keys.reserve(nodes.size());
    
    for(int i = 0; i < nodes.size(); ++i) {
      keys.push_back(nodes[i]->key);
    }
    return keys;
  }

  static vector<pair<Key, Value> > node_traverse_items_in_order(const NodePtr& node)
  {
    vector<NodePtr> nodes;
    nodes.reserve(node->size);
    node_traverse_in_order(node, nodes);
    
    vector<Key> items;
    items.reserve(nodes.size());
    
    for(int i = 0; i < nodes.size(); ++i) {
      items.push_back(pair<Key, Value>(nodes[i]->key, nodes[i]->value));
    }
    return items;
  }
};

/*
Persistent map backed by a weight-balanced tree.
The lookup method throws an error if the key is not found. Use
the contains method if you aren't sure whether the key exists.
*/
template <typename Key, typename Value>
class PMap
{
  typedef typename Node<Key, Value>::NodePtr NodePtr;
  
  NodePtr root;
  
  PMap(NodePtr root) : root(root) {} 

public:
  PMap() : root(new Node<Key, Value>()) {}
  
  bool contains(const Key& key)
    { return Node<Key, Value>::node_contains(root, key); }
    
  Value lookup(const Key& key)
    { return Node<Key, Value>::node_lookup(root, key); }
  
  PMap insert(const Key& key, const Value& value)
    { return PMap(Node<Key, Value>::node_insert(root, key, value)); }
  
  /*
  adjust :: (PMap k v) -> k -> (v -> v) -> PMap k v

  Returns a new PMap obtained from this one by applying the given
  function to the value at the given key. Returns the original PMap
  unchanged if the key is not present. The name is chosen by
  analogy to Data.PMap.adjust from the Haskell standard library.
  */
  template <class Function>
  PMap adjust(const Key& key, const Function& f)
    { return PMap(Node<Key, Value>::node_adjust(root, key, f)); }
  
  PMap remove(const Key& key)
    { return PMap(Node<Key, Value>::node_remove(root, key)); }

  size_t size() { return root->size; }
  
  vector<Key> keys()
    { return Node<Key, Value>::node_traverse_keys_in_order(root); }
  
  vector<pair<Key, Value> > items()
    { return Node<Key, Value>::node_traverse_items_in_order(root); }  
};

/*
Persistent set backed by a weight-balanced tree.
At present, happens to be implemented just like a PMap, but with the
values always being True. In principle could be impemented more
efficiently by specializing the nodes not to store values at all.
*/
template <typename Key>
class PSet
{
  typedef typename Node<Key, bool>::NodePtr NodePtr;
  
  NodePtr root;
  
  PSet(NodePtr root) : root(root) {} 

public:
  PSet() : root(new Node<Key, bool>()) {}
  
  bool contains(const Key& key)
    { return Node<Key, bool>::node_contains(root, key); }
  
  PSet insert(const Key& key)
    { return Node<Key, bool>::PSet(node_insert(root, key, true)); }
  
  /*
  adjust :: (PSet k v) -> k -> (v -> v) -> PSet k v

  Returns a new PSet obtained from this one by applying the given
  function to the bool at the given key. Returns the original PSet
  unchanged if the key is not present. The name is chosen by
  analogy to Data.PSet.adjust from the Haskell standard library.
  */
  template <class Function>
  PSet adjust(const Key& key, const Function& f)
    { return PSet(Node<Key, bool>::node_adjust(root, key, f)); }
  
  PSet remove(const Key& key)
    { return PSet(Node<Key, bool>::node_remove(root, key)); }

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
