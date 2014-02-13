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
const string& VentureValue::getSymbol() const { cannotConvertType(this,"symbol"); assert(false); throw "no return"; }
const vector<VentureValuePtr>& VentureValue::getArray() const { cannotConvertType(this,"array"); assert(false); throw "no return"; }

const VentureValuePtr& VentureValue::getCar() const { cannotConvertType(this,"pair"); assert(false); throw "no return"; }
const VentureValuePtr& VentureValue::getCdr() const { cannotConvertType(this,"pair"); assert(false); throw "no return"; }
  
const Simplex& VentureValue::getSimplex() const { cannotConvertType(this,"simplex"); assert(false); throw "no return"; }
const VentureValuePtrMap<VentureValuePtr>& VentureValue::getDictionary() const { cannotConvertType(this,"dictionary"); assert(false); throw "no return"; }
const MatrixXd& VentureValue::getMatrix() const { cannotConvertType(this,"matrix"); assert(false); throw "no return"; }

const vector<ESR>& VentureValue::getESRs() const { cannotConvertType(this,"requests"); assert(false); throw "no return"; }
const vector<shared_ptr<LSR> >& VentureValue::getLSRs() const { cannotConvertType(this,"requests"); assert(false); throw "no return"; }

bool VentureValue::equals(const VentureValuePtr & other) const { return false; assert(false); throw "no return"; }
size_t VentureValue::hash() const { assert(false); assert(false); throw "no return"; }
