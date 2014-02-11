#ifndef TYPES_H
#define TYPES_H

#include <boost/shared_ptr.hpp>
#include <boost/unordered_map.hpp>
#include <vector>
#include <map>
#include <set>

using boost::unordered_map;
using boost::shared_ptr;
using std::vector;
using std::map;
using std::set;
using std::string;
using std::size_t;
using std::pair;
using std::make_pair;

struct VentureValue;
struct Node;

typedef int DirectiveID;
typedef shared_ptr<VentureValue> VentureValuePtr;
typedef VentureValuePtr ScopeID;
typedef VentureValuePtr BlockID;
typedef VentureValuePtr FamilyID;
typedef shared_ptr<Node> RootOfFamily;
typedef vector<double> Simplex;

/* TODO I keep oscillating on these. 
   One convention could be to only use this shortcut for VentureValuePtr.
   Another could be to only use it for all VentureValues, which would include
   SP,Environment,SPRef,and others. */

//typedef shared_ptr<VentureSP> VentureSPPtr;
//typedef shared_ptr<VentureEnvironment> VentureEnvironmentPtr;

#endif
