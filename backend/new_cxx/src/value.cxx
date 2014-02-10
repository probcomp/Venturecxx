void cannotConvertType(VentureValuePtr type,string target)
{
  string msg = "Cannot convert [" + typeid(type) + "] to [" + target + "]";
  throw exception(msg.c_str());
}

double VentureValue::getDouble() { cannotConvertType(this,"double"); }
int VentureValue::getInt() { cannotConvertType(this,"int"); }
int VentureValue::getAtom() { cannotConvertType(this,"atom"); }
bool VentureValue::getBool() { cannotConvertType(this,"bool"); }
string VentureValue::getSymbol() { cannotConvertType(this,"symbol"); }
vector<VentureValuePtr> VentureValue::getArray() { cannotConvertType(this,"array"); }
pair<VentureValuePtr,VentureValuePtr> VentureValue::getPair() { cannotConvertType(this,"pair"); }
simplex VentureValue::getSimplex() { cannotConvertType(this,"simplex"); }
map<VentureValuePtr,VentureValuePtr> VentureValue::getDictionary() { cannotConvertType(this,"dictionary"); }
MatrixXd VentureValue::getMatrix() { cannotConvertType(this,"matrix"); }
pair<vector<ESR>,vector<LSR *> > VentureValue::getRequests() { cannotConvertType(this,"requests"); }
