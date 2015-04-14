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

namespace persistent
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
    left(left),
    key(key),
    value(value),
    right(right),
    size(left->size + right->size + 1)
  {}
  
  bool isEmpty() const { return size == 0; }
  
  NodePtr left;
  Key key;
  Value value;
  NodePtr right;
  size_t size;

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
  
  template <typename Comp>
  static bool node_contains(const NodePtr& node, const Key& key, const Comp& comp)
  {
    if (node->isEmpty())
    {
      return false;
    }
    else if (comp(key, node->key))
    {
      return node_contains(node->left, key, comp);
    }
    else if (comp(node->key, key))
    {
      return node_contains(node->right, key, comp);
    }
    else
    {
      return true;
    }
  }

  template <typename Comp>
  static Value node_lookup(const NodePtr& node, const Key& key, const Comp& comp)
  {
    if (node->isEmpty())
    {
      assert(false);
      throw "Key does not exist.";
    }
    else if (comp(key, node->key))
    {
      return node_lookup(node->left, key, comp);
    }
    else if (comp(node->key, key))
    {
      return node_lookup(node->right, key, comp);
    }
    else
    {
      return node->value;
    }
  }

  template <typename Comp>
  static NodePtr node_insert(const NodePtr& node, const Key& key, const Value& value, const Comp& comp)
  {
    if (node->isEmpty())
    {
      return NodePtr(new Node(NodePtr(new Node()), key, value, NodePtr(new Node())));
    }
    else if (comp(key, node->key))
    {
      return t_join(node_insert(node->left, key, value, comp),
                    node->key, node->value, node->right);
    }
    else if (comp(node->key, key))
    {
      return t_join(node->left, node->key, node->value,
                    node_insert(node->right, key, value, comp));
    }
    else
    {
      return NodePtr(new Node(node->left, key, value, node->right));
    }
  }

  template <class Function, typename Comp>
  static NodePtr node_adjust(const NodePtr& node, const Key& key, const Function& f, const Comp& comp)
  {
    if (node->isEmpty())
    {
      // TODO Optimize the not-found case by not reconstructing the tree
      // on the way up?
      return node;
    }
    else if (comp(key, node->key))
    {
      return NodePtr(new Node(node_adjust(node->left, key, f, comp),
                  node->key, node->value, node->right));
    }
    else if (comp(node->key, key))
    {
      return NodePtr(new Node(node->left, node->key, node->value,
                  node_adjust(node->right, key, f, comp)));
    }
    else
    {
      return NodePtr(new Node(node->left, key, f(node->value), node->right));
    }
  }

  template <typename Comp>
  static NodePtr node_remove(const NodePtr& node, const Key& key, const Comp& comp)
  {
    if (node->isEmpty())
    {
      return node;
    }
    else if (comp(key, node->key))
    {
      return t_join(node_remove(node->left, key, comp),
                    node->key, node->value, node->right);
    }
    else if (comp(node->key, key))
    {
      return t_join(node->left, node->key, node->value,
                    node_remove(node->right, key, comp));
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
    
    for(size_t i = 0; i < nodes.size(); ++i) {
      keys.push_back(nodes[i]->key);
    }
    return keys;
  }

  static vector<pair<Key, Value> > node_traverse_items_in_order(const NodePtr& node)
  {
    vector<NodePtr> nodes;
    nodes.reserve(node->size);
    node_traverse_in_order(node, nodes);
    
    vector<pair<Key, Value> > items;
    items.reserve(nodes.size());
    
    for(size_t i = 0; i < nodes.size(); ++i) {
      items.push_back(pair<Key, Value>(nodes[i]->key, nodes[i]->value));
    }
    return items;
  }
};

};



#endif
