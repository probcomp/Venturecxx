#include "value.h"

void cannotConvertType(const VentureValue * obj, string target)
{
  string msg = "Cannot convert [unknown] to [" + target + "]";
  throw msg;
}

double VentureValue::getDouble() const { cannotConvertType(this,"double"); throw "no return"; }
int VentureValue::getInt() const { cannotConvertType(this,"int"); throw "no return"; }
int VentureValue::getAtom() const { cannotConvertType(this,"atom"); throw "no return"; }
bool VentureValue::getBool() const { cannotConvertType(this,"bool"); throw "no return"; }
string VentureValue::getSymbol() const { cannotConvertType(this,"symbol"); throw "no return"; }
vector<VentureValuePtr> VentureValue::getArray() const { cannotConvertType(this,"array"); throw "no return"; }
pair<VentureValuePtr,VentureValuePtr> VentureValue::getPair() const { cannotConvertType(this,"pair"); throw "no return"; }
Simplex VentureValue::getSimplex() const { cannotConvertType(this,"simplex"); throw "no return"; }
unordered_map<VentureValuePtr,VentureValuePtr> VentureValue::getDictionary() const { cannotConvertType(this,"dictionary"); throw "no return"; }
MatrixXd VentureValue::getMatrix() const { cannotConvertType(this,"matrix"); throw "no return"; }
pair<vector<ESR>,vector<LSR *> > VentureValue::getRequests() const { cannotConvertType(this,"requests"); throw "no return"; }
bool VentureValue::equals(const shared_ptr<const VentureValue> & other) const { return false; throw "no return"; }
size_t VentureValue::hash() const { assert(false); throw "no return"; }
