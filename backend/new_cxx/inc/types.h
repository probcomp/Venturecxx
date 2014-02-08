#ifndef TYPES_H
#define TYPES_H

#include <boost/shared_ptr.hpp>

struct VentureValue;
struct VentureSP;
struct VentureEnvironment;

struct Node;

typedef int DirectiveID;

typedef boost::shared_ptr<VentureValue> VentureValuePtr;
typedef boost::shared_ptr<VentureSP> VentureSPPtr;
typedef boost::shared_ptr<VentureEnvironment> VentureEnvironmentPtr;


typedef VentureValuePtr ScopeID;
typedef VentureValuePtr BlockID;
typedef VentureValuePtr FamilyID;
typedef boost::shared_ptr<Node> RootOfFamily;
typedef vector<double> simplex;

#endif
