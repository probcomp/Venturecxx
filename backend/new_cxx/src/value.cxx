#include "value.h"
#include "values.h"
#include "sp.h"
#include "sprecord.h"
#include "env.h"
#include <boost/lexical_cast.hpp>

int getValueTypeRank(const VentureValue * v);
void cannotConvertType(const VentureValue * obj, string target)
{
  throw "Cannot convert " + obj->toString() + " to [" + target + "]";
}

bool VentureValue::hasDouble() const { return false; }

double VentureValue::getDouble() const
{
  cannotConvertType(this,"double"); assert(false); throw "no return";
}

bool VentureValue::hasInt() const { return false; }
long VentureValue::getInt() const
{
  cannotConvertType(this,"int"); assert(false); throw "no return";
}

double VentureValue::getProbability() const
{
  double x;
  try {
    x = getDouble();
  }
  catch (string) {
    cannotConvertType(this,"probability"); assert(false); throw "no return";
  }
  if (0 <= x && x <= 1) {
    return x;
  }
  else {
    throw "Probability out of range " + toString();
  }
}

int VentureValue::getAtom() const
{
  cannotConvertType(this,"atom"); assert(false); throw "no return";
}

bool VentureValue::isBool() const { return false; }
bool VentureValue::getBool() const
{
  cannotConvertType(this,"bool"); assert(false); throw "no return";
}

bool VentureValue::hasSymbol() const { return false; }
const string& VentureValue::getSymbol() const
{
  cannotConvertType(this,"symbol"); assert(false); throw "no return";
}


const VentureValuePtr& VentureValue::getFirst() const
{
  cannotConvertType(this,"pair"); assert(false); throw "no return";
}

const VentureValuePtr& VentureValue::getRest() const
{
  cannotConvertType(this,"pair"); assert(false); throw "no return";
}

  
vector<VentureValuePtr> VentureValue::getArray() const
{
  cannotConvertType(this,"array"); assert(false); throw "no return";
}

const Simplex& VentureValue::getSimplex() const
{
  cannotConvertType(this,"simplex"); assert(false); throw "no return";
}

const MapVVPtrVVPtr& VentureValue::getDictionary() const
{
  cannotConvertType(this,"dictionary"); assert(false); throw "no return";
}

VectorXd VentureValue::getVector() const
{
  cannotConvertType(this,"vector"); assert(false); throw "no return";
}


MatrixXd VentureValue::getMatrix() const
{
  cannotConvertType(this,"matrix"); assert(false); throw "no return";
}


boost::python::dict VentureValue::toPython(Trace * trace) const
{ 
  boost::python::dict value;
  value["type"] = "unknown";
  value["value"] = "opaque";
  return value;
}


bool VentureValue::operator<(const VentureValuePtr & rhs) const 
{
  int t1 = getValueTypeRank(this);
  int t2 = getValueTypeRank(rhs.get());
  if (t1 < t2) { return true; }
  else if (t2 < t1) { return false; }
  else { return ltSameType(rhs); }
}

bool VentureValue::ltSameType(const VentureValuePtr & rhs) const { throw "Cannot compare " + toString(); }


bool VentureValue::equals(const VentureValuePtr & other) const 
{
  int t1 = getValueTypeRank(this);
  int t2 = getValueTypeRank(other.get());
  if (t1 != t2) { return false; }
  else { return equalsSameType(other); }
}

bool VentureValue::equalsSameType(const VentureValuePtr & rhs) const { throw "Cannot compare " + toString(); }

size_t VentureValue::hash() const
{
  assert(false); assert(false); throw "no return";
}

VentureValuePtr VentureValue::lookup(VentureValuePtr index) const { throw "Cannot look things up in " + toString(); }
bool VentureValue::contains(VentureValuePtr index) const { throw "Cannot look for things in " + toString(); }
int VentureValue::size() const { throw "Cannot measure size of " + toString(); }


const vector<ESR>& VentureValue::getESRs() const
{
  cannotConvertType(this,"requests"); assert(false); throw "no return";
}

const vector<shared_ptr<LSR> >& VentureValue::getLSRs() const
{
  cannotConvertType(this,"requests"); assert(false); throw "no return";
}


Node * VentureValue::getNode() const
{
  cannotConvertType(this,"node") ; assert(false); throw "no return";
}


shared_ptr<SPAux> VentureValue::getSPAux() const
{
  cannotConvertType(this,"sprecord") ; assert(false); throw "no return";
}

string VentureValue::asExpression() const { return toString(); }

int getValueTypeRank(const VentureValue * v)
{
  // Note: differs slightly from 
  if (dynamic_cast<const VentureNumber *>(v)) { return 0; }

  else if (dynamic_cast<const VentureAtom *>(v)) { return 1; }
  else if (dynamic_cast<const VentureBool *>(v)) { return 2; }
  else if (dynamic_cast<const VentureSymbol *>(v)) { return 3; }

  else if (dynamic_cast<const VentureNil *>(v)) { return 4; }
  else if (dynamic_cast<const VenturePair *>(v)) { return 5; }
  else if (dynamic_cast<const VentureArray *>(v)) { return 6; }

  else if (dynamic_cast<const VentureSimplex *>(v)) { return 7; }
  else if (dynamic_cast<const VentureDictionary *>(v)) { return 8; }
  else if (dynamic_cast<const VentureMatrix *>(v)) { return 9; }
  else if (dynamic_cast<const VentureSPRef *>(v)) { return 10; }

  else if (dynamic_cast<const VentureEnvironment *>(v)) { return 11; }
  else if (dynamic_cast<const VentureSPRecord *>(v)) { return 12; }
  else if (dynamic_cast<const VentureRequest *>(v)) { return 13; }
  else if (dynamic_cast<const VentureNode *>(v)) { return 14; }
  else if (dynamic_cast<const VentureID *>(v)) { return 15; }
  else { throw "Unknown type '" + v->toString() + "'"; return -1; }
}
