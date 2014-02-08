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

/* TODO I keep oscillating on these. 
   One convention could be to only use this shortcut for VentureValuePtr.
   Another could be to only use it for all VentureValues, which would include
   SP,Environment,SPRef,and others. */

//typedef shared_ptr<VentureSP> VentureSPPtr;
//typedef shared_ptr<VentureEnvironment> VentureEnvironmentPtr;

#endif
