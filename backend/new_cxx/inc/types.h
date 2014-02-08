#ifndef TYPES_H
#define TYPES_H

#include <boost/shared_ptr.hpp>

using boost::shared_ptr;

struct VentureValue;
struct Node;

typedef int DirectiveID;
typedef shared_ptr<VentureValue> VentureValuePtr;
typedef VentureValuePtr ScopeID;
typedef VentureValuePtr BlockID;
typedef VentureValuePtr FamilyID;
typedef shared_ptr<Node> RootOfFamily;
typedef vector<double> simplex;

#endif
