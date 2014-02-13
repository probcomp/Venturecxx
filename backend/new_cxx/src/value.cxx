#include "value.h"
#include <iostream>

using std::cout;
using std::endl;

void cannotConvertType(const VentureValue * obj, string target)
{
  cout << "Cannot convert [unknown] to [" + target + "]" << endl;
  assert(false);
}

double VentureValue::getDouble() const { cannotConvertType(this,"double"); assert(false); throw "no return"; }
int VentureValue::getInt() const { cannotConvertType(this,"int"); assert(false); throw "no return"; }
int VentureValue::getAtom() const { cannotConvertType(this,"atom"); assert(false); throw "no return"; }
bool VentureValue::getBool() const { cannotConvertType(this,"bool"); assert(false); throw "no return"; }
string VentureValue::getSymbol() const { cannotConvertType(this,"symbol"); assert(false); throw "no return"; }
vector<VentureValuePtr> VentureValue::getArray() const { cannotConvertType(this,"array"); assert(false); throw "no return"; }
pair<VentureValuePtr,VentureValuePtr> VentureValue::getPair() const { cannotConvertType(this,"pair"); assert(false); throw "no return"; }
Simplex VentureValue::getSimplex() const { cannotConvertType(this,"simplex"); assert(false); throw "no return"; }
const VentureValuePtrMap<VentureValuePtr>& VentureValue::getDictionary() const { cannotConvertType(this,"dictionary"); assert(false); throw "no return"; }
MatrixXd VentureValue::getMatrix() const { cannotConvertType(this,"matrix"); assert(false); throw "no return"; }
pair<vector<ESR>,vector<shared_ptr<LSR> > > VentureValue::getRequests() const { cannotConvertType(this,"requests"); assert(false); throw "no return"; }
bool VentureValue::equals(const shared_ptr<const VentureValue> & other) const { return false; assert(false); throw "no return"; }
size_t VentureValue::hash() const { assert(false); assert(false); throw "no return"; }
