#include "value.h"

void cannotConvertType(const VentureValue * obj, string target)
{
  string msg = "Cannot convert [unknown] to [" + target + "]";
  throw msg;
}

double VentureValue::getDouble() const { cannotConvertType(this,"double"); }
int VentureValue::getInt() const { cannotConvertType(this,"int"); }
int VentureValue::getAtom() const { cannotConvertType(this,"atom"); }
bool VentureValue::getBool() const { cannotConvertType(this,"bool"); }
string VentureValue::getSymbol() const { cannotConvertType(this,"symbol"); }
vector<VentureValuePtr> VentureValue::getArray() const { cannotConvertType(this,"array"); }
pair<VentureValuePtr,VentureValuePtr> VentureValue::getPair() const { cannotConvertType(this,"pair"); }
Simplex VentureValue::getSimplex() const { cannotConvertType(this,"simplex"); }
unordered_map<VentureValuePtr,VentureValuePtr> VentureValue::getDictionary() const { cannotConvertType(this,"dictionary"); }
MatrixXd VentureValue::getMatrix() const { cannotConvertType(this,"matrix"); }
pair<vector<ESR>,vector<LSR *> > VentureValue::getRequests() const { cannotConvertType(this,"requests"); }
bool VentureValue::equals(shared_ptr<const VentureValue> & other) const { return false; }
size_t VentureValue::hash() const { assert(false); }
