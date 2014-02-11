// TODO typeid(...) might be C++11
void cannotConvertType(VentureValuePtr type,string target)
{
  string msg = "Cannot convert [" + typeid(type) + "] to [" + target + "]";
  throw exception(msg.c_str());
}

double VentureValue::getDouble() const { cannotConvertType(this,"double"); }
int VentureValue::getInt() const { cannotConvertType(this,"int"); }
int VentureValue::getAtom() const { cannotConvertType(this,"atom"); }
bool VentureValue::getBool() const { cannotConvertType(this,"bool"); }
string VentureValue::getSymbol() const { cannotConvertType(this,"symbol"); }
vector<VentureValuePtr> VentureValue::getArray() const { cannotConvertType(this,"array"); }
pair<VentureValuePtr,VentureValuePtr> VentureValue::getPair() const { cannotConvertType(this,"pair"); }
simplex VentureValue::getSimplex() const { cannotConvertType(this,"simplex"); }
map<VentureValuePtr,VentureValuePtr> VentureValue::getDictionary() { cannotConvertType(this,"dictionary"); }
MatrixXd VentureValue::getMatrix() const { cannotConvertType(this,"matrix"); }
pair<vector<ESR>,vector<LSR *> > VentureValue::getRequests() { cannotConvertType(this,"requests"); }
bool equals(const VentureValuePtr & other) const { return false; }
