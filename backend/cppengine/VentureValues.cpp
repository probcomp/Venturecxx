#include "HeaderPre.h"
#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"

void VentureValue::CheckMyData(VentureValue* venture_value) {
  // This is standard blank checker.
}
void VentureCount::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetInteger() < 0) {
    // Disabled just for now, before we have VentureNumber.
    // throw std::runtime_error("VentureCount should be non-negative.");
  }
}
void VentureReal::CheckMyData(VentureValue* venture_value) {
  venture_value->GetReal();
}
void VentureProbability::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetReal() < 0.0 || venture_value->GetReal() > 1.0) { // Add acceptable epsilon error?
    throw std::runtime_error("VentureProbability should be non-negative and not more than 1.0.");
  }
}
void VentureAtom::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetInteger() < 0) {
    throw std::runtime_error("VentureAtom should be non-negative.");
  }
}

void VentureSimplexPoint::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetType() == SIMPLEXPOINT) {
    throw std::runtime_error("VentureSimplexPoint should be represented only by itself.");
  }
}
void VentureSmoothedCountVector::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetType() == SMOOTHED_COUNT_VECTOR) {
    throw std::runtime_error("VentureSmoothedCountVector should be represented only by itself.");
  }
}
void VentureSmoothedCount::CheckMyData(VentureValue* venture_value) {
  if (venture_value->GetReal() < 0.0) { // Add acceptable epsilon error.
    throw std::runtime_error("VentureSmoothedCount should be nonnegative.");
  }
}

// *** Constructors ***
VentureValue::VentureValue() {
  // cout << "Create: " << this << endl;
}
VentureBoolean::VentureBoolean(const bool data) : data(data) {}
VentureCount::VentureCount(const int data) : data(data) {
  this->CheckMyData(this);
}
VentureReal::VentureReal(const real data) : data(data) {}
VentureProbability::VentureProbability(const real data) : data(data) {
  this->CheckMyData(this);
}
VentureSimplexPoint::VentureSimplexPoint(vector<real>& input_data) {
  // : data(SOMEFUNCTION(data)) -- it should be implemented in this way?
  // this->CheckMyData(this); // Blank. // FIXME!
  size_t dimension = input_data.size();
  if (dimension == 0) {
    throw std::runtime_error("VentureSimplexPoint should be at least one-dimensional.");
  }
  data.reserve(dimension);

  real sum = 0.0;
  for (size_t index = 0; index < dimension; index++) {
    real weight = input_data[index];
    if (weight < 0.0) { // Add acceptable epsilon error?
      throw std::runtime_error("VentureSimplexPoint element should be non-negative.");
    }
    data.push_back(weight);
    sum += weight;
  }
  if (fabs(sum - 1.0) > comparison_epsilon) {
    throw std::runtime_error("Sum of VentureSimplexPoint elements should be equal to 1.0.");
  }
}
VentureSmoothedCountVector::VentureSmoothedCountVector(vector<real>& input_data) {
  // : data(SOMEFUNCTION(data)) -- it should be implemented in this way?
  // this->CheckMyData(this); // Blank. // FIXME!
  size_t dimension = input_data.size();
  if (dimension == 0) {
    throw std::runtime_error("VentureSmoothedCountVector should be at least one-dimensional.");
  }
  data.reserve(dimension);

  for (size_t index = 0; index < dimension; index++) {
    real weight = input_data[index];
    if (weight <= 0.0) { // Add acceptable epsilon error?
      throw std::runtime_error("VentureSmoothedCountVector element should be positive.");
    }
    data.push_back(weight);
  }
}

VentureAtom::VentureAtom(const int data) : data(data) {
  this->CheckMyData(this);
}

VentureSmoothedCount::VentureSmoothedCount(const real data) : data(data) {
  this->CheckMyData(this);
}
VentureNil::VentureNil() : VentureList(shared_ptr<VentureValue>()) {}

VentureList::VentureList(shared_ptr<VentureValue> car)
  : car(car), cdr(NIL_INSTANCE) {}

VentureList::VentureList(shared_ptr<VentureValue> car, shared_ptr<VentureList> cdr)
  : car(car), cdr(cdr) {}

VentureXRP::VentureXRP(shared_ptr<XRP> xrp)
  : xrp(xrp) {}

VentureSymbol::VentureSymbol(const string& symbol) : symbol(symbol) {
  this->CheckMyData(this); // Blank.
  if (legal_SYMBOL_name(symbol) == false) {
    throw std::runtime_error(("Incorrect symbol: " + symbol + ".").c_str());
  }
}

VentureLambda::VentureLambda(shared_ptr<VentureList> formal_arguments,
              shared_ptr<NodeEvaluation> expressions,
              shared_ptr<NodeEnvironment> scope_environment)
  : formal_arguments(formal_arguments), expressions(expressions), scope_environment(scope_environment) {}

// *** Destructors ***
VentureValue::~VentureValue() {
  //cout << "Delete: " << this << " " << GetType() << " " << GetString() << endl;
}
// From VentureValues.h
/*
VentureBoolean::~VentureBoolean() { cout << "Deleting: VentureBoolean" << endl; }
VentureCount::~VentureCount() { cout << "Deleting: VentureCount" << endl; }
VentureReal::~VentureReal() { cout << "Deleting: VentureReal" << endl; }
VentureProbability::~VentureProbability() { cout << "Deleting: VentureProbability" << endl; }
VentureAtom::~VentureAtom() { cout << "Deleting: VentureAtom" << endl; }
VentureSimplexPoint::~VentureSimplexPoint() { cout << "Deleting: VentureSimplexPoint" << endl; }
VentureSmoothedCount::~VentureSmoothedCount() { cout << "Deleting: VentureSmoothedCount" << endl; }
VentureList::~VentureList() { cout << "Deleting: VentureList" << endl; }
VentureNil::~VentureNil() { cout << "Deleting: VentureNil" << endl; }
VentureSymbol::~VentureSymbol() { cout << "Deleting: VentureSymbol" << endl; }
VentureLambda::~VentureLambda() { cout << "Deleting: VentureLambda" << endl; }
VentureXRP::~VentureXRP() { cout << "Deleting: VentureXRP" << endl; }
*/
VentureBoolean::~VentureBoolean() {}
VentureCount::~VentureCount() {}
VentureReal::~VentureReal() {}
VentureProbability::~VentureProbability() {}
VentureAtom::~VentureAtom() {}

VentureSimplexPoint::~VentureSimplexPoint() {}
VentureSmoothedCountVector::~VentureSmoothedCountVector() {}
VentureSmoothedCount::~VentureSmoothedCount() {}
VentureList::~VentureList() {}
VentureNil::~VentureNil() {}
VentureSymbol::~VentureSymbol() {}
VentureLambda::~VentureLambda() {}
VentureXRP::~VentureXRP() {}

// *** GetType ***
VentureDataTypes VentureValue::GetType() { return UNDEFINED_TYPE; }
VentureDataTypes VentureBoolean::GetType() { return BOOLEAN; }
VentureDataTypes VentureCount::GetType() { return COUNT; }
VentureDataTypes VentureReal::GetType() { return REAL; }
VentureDataTypes VentureProbability::GetType() { return PROBABILITY; }
VentureDataTypes VentureAtom::GetType() { return ATOM; }
VentureDataTypes VentureSimplexPoint::GetType() { return SIMPLEXPOINT; }
VentureDataTypes VentureSmoothedCountVector::GetType() { return SMOOTHED_COUNT_VECTOR; }
VentureDataTypes VentureSmoothedCount::GetType() { return SMOOTHEDCOUNT; }
VentureDataTypes VentureList::GetType() { return LIST; }
VentureDataTypes VentureNil::GetType() { return NIL; }
VentureDataTypes VentureSymbol::GetType() { return SYMBOL; }
VentureDataTypes VentureXRP::GetType() { return XRP_REFERENCE; }
VentureDataTypes VentureLambda::GetType() { return LAMBDA; }

// *** GetReal ***
real VentureValue::GetReal() {
  throw std::runtime_error("GetReal() is not implemented for this type (type: " + boost::lexical_cast<string>(this->GetType()) + ").");
}
real VentureCount::GetReal() {
  return data;
}
real VentureReal::GetReal() {
  return data;
}
real VentureProbability::GetReal() {
  return data;
}
real VentureAtom::GetReal() {
  return data;
}
real VentureSmoothedCount::GetReal() {
  return data;
}
real VentureBoolean::GetReal() { // Should be deleted.
  if (data == true) {
    return 1.0;
  } else {
    return 0.0;
  }
}

// *** GetInteger ***
int VentureValue::GetInteger() {
  throw std::runtime_error(("GetInteger() is not implemented for this type" + boost::lexical_cast<string>(this->GetType()) + ".").c_str());
}
int VentureCount::GetInteger() {
  return data;
}
int VentureAtom::GetInteger() {
  return data;
}
int VentureBoolean::GetInteger() {
  return data;
}

// *** GetString ***
string VentureValue::GetString() { return "UNDEFINED"; }
string VentureBoolean::GetString() {
  if (data == false) {
    return "#f";
  } else {
    return "#t";
  }
}
string VentureCount::GetString() { return boost::lexical_cast<string>(data); }
string VentureReal::GetString() { return boost::lexical_cast<string>(data); }
string VentureAtom::GetString() { return boost::lexical_cast<string>(data); }
string VentureProbability::GetString() { return boost::lexical_cast<string>(data); }
string VentureSimplexPoint::GetString() {
  string output = "sp[";
  for (size_t index = 0; index < data.size(); index++)
  {
    if (index > 0) {
      output += ",";
    }
    output += boost::lexical_cast<string>(data[index]);
  }
  output += "]";
  return output;
}
string VentureSmoothedCountVector::GetString() {
  string output = "vsc[";
  for (size_t index = 0; index < data.size(); index++)
  {
    if (index > 0) {
      output += ",";
    }
    output += boost::lexical_cast<string>(data[index]);
  }
  output += "]";
  return output;
}
string VentureSmoothedCount::GetString() { return boost::lexical_cast<string>(data); }
string VentureNil::GetString() { return "#nil"; }
string VentureSymbol::GetString() { return symbol; }
string VentureLambda::GetString() { return "LAMBDA"; }
string VentureXRP::GetString() { return "XRP_REFERENCE"; }
string VentureList::GetString() {
  std::string output("(");
  shared_ptr<VentureList> iterator = dynamic_pointer_cast<VentureList>(this->shared_from_this());
  while (iterator->GetType() != NIL) {
    assert(iterator != NIL_INSTANCE);
    if (iterator != this->shared_from_this()) { output += " "; }
    output += Stringify(iterator->car);
    iterator = iterator->cdr;
  }
  output += ")";
  return output;
}

// *** Returning Python objects ***
PyObject* VentureValue::GetAsPythonObject() { throw std::runtime_error("Should not be called (2)."); }
PyObject* VentureBoolean::GetAsPythonObject() { if (this->data) { Py_INCREF(Py_True); return Py_True; } else { Py_INCREF(Py_False); return Py_False; } }
PyObject* VentureCount::GetAsPythonObject() { return Py_BuildValue("i", this->data); }
PyObject* VentureReal::GetAsPythonObject() { return Py_BuildValue("d", this->data); }
PyObject* VentureAtom::GetAsPythonObject() { return Py_BuildValue("s", (string("a[") + string(boost::lexical_cast<string>(this->data)) + string("]")).c_str()); }
PyObject* VentureProbability::GetAsPythonObject() { return Py_BuildValue("d", this->data); }
PyObject* VentureSimplexPoint::GetAsPythonObject() {
  PyObject* returning_tuple = PyTuple_New(data.size());
  for (size_t index = 0; index < data.size(); index++) {
    PyTuple_SetItem(returning_tuple, index, Py_BuildValue("d", data[index]));
  }
  return returning_tuple;
}
PyObject* VentureSmoothedCountVector::GetAsPythonObject() {
  PyObject* returning_tuple = PyTuple_New(data.size());
  for (size_t index = 0; index < data.size(); index++) {
    PyTuple_SetItem(returning_tuple, index, Py_BuildValue("d", data[index]));
  }
  return returning_tuple;
}
PyObject* VentureSmoothedCount::GetAsPythonObject() { return Py_BuildValue("d", this->data); }
PyObject* VentureNil::GetAsPythonObject() { return Py_BuildValue("[]"); }
PyObject* VentureSymbol::GetAsPythonObject() { return Py_BuildValue("s", this->symbol.c_str()); }
PyObject* VentureLambda::GetAsPythonObject() { return Py_BuildValue("s", "LAMBDA"); } // Specify LAMBDA's reference.
PyObject* VentureXRP::GetAsPythonObject() { return Py_BuildValue("s", "XRP_REFERENCE"); } // Specify LAMBDA's reference.
PyObject* VentureList::GetAsPythonObject() {
  vector< PyObject* > elements;
  shared_ptr<VentureList> iterator = dynamic_pointer_cast<VentureList>(this->shared_from_this());
  while (iterator->GetType() != NIL) {
    assert(iterator != NIL_INSTANCE);
    elements.push_back(iterator->car->GetAsPythonObject());
    iterator = iterator->cdr;
  }
  PyObject* returning_list = PyList_New(elements.size());
  for (size_t index = 0; index < elements.size(); index++) {
    PyList_SetItem(returning_list, index, elements[index]);
  }
  return returning_list;
}

// *** Function for VentureSymbol ***
bool is_not_legal_SYMBOL_character(char c)
{
  //return !(isalnum(c) || (c == '-'));
  return !(isgraph(c));
}
bool legal_SYMBOL_name(const string& str)
{
  return find_if(str.begin(), str.end(), is_not_legal_SYMBOL_character) == str.end();
}

// *** Function for VentureType control and transfer ***
template <typename T>
bool VerifyVentureType(shared_ptr<VentureValue> value) {
  return dynamic_pointer_cast<T>(value) != shared_ptr<T>();
}
template <typename T>
void AssertVentureType(shared_ptr<VentureValue> value) {
  if (!VerifyVentureType<T>(value)) {
    throw std::runtime_error(("Assertion: not the right type: has " + boost::lexical_cast<string>(value->GetType()) + ", we want '...'.").c_str());
  }
}
template <typename T>
shared_ptr<T> ToVentureType(shared_ptr<VentureValue> value) {
  AssertVentureType<T>(value);
  return dynamic_pointer_cast<T>(value);
}

void __BlankFunction1() { // Why without this function the g++ (Unix) with -O2 returns that it cannot find them?
  ToVentureType<VentureAtom>(shared_ptr<VentureValue>());
  ToVentureType<VentureLambda>(shared_ptr<VentureValue>());
  ToVentureType<VentureSymbol>(shared_ptr<VentureValue>());
  ToVentureType<VentureReal>(shared_ptr<VentureValue>());
  ToVentureType<VentureCount>(shared_ptr<VentureValue>());
  ToVentureType<VentureBoolean>(shared_ptr<VentureValue>());
  ToVentureType<VentureList>(shared_ptr<VentureValue>());
  ToVentureType<VentureSimplexPoint>(shared_ptr<VentureValue>());
  ToVentureType<VentureSmoothedCountVector>(shared_ptr<VentureValue>());
  ToVentureType<VentureXRP>(shared_ptr<VentureValue>());
  ToVentureType<VenturePythonObject>(shared_ptr<VentureValue>());
  ToVentureType<VentureString>(shared_ptr<VentureValue>());
#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
  ToVentureType<VentureExternalXRPObject>(shared_ptr<VentureValue>());
#endif
}

// *** CompareByValue ***
bool VentureValue::CompareByValue(shared_ptr<VentureValue> another) {
  throw std::runtime_error("Should not be called (1).");
}
bool VentureSymbol::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->symbol == ToVentureType<VentureSymbol>(another)->symbol);
}
bool VentureBoolean::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureBoolean>(another)->data);
}
bool VentureCount::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureCount>(another)->data);
}
bool VentureReal::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureReal>(another)->data);
}
bool VentureProbability::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureProbability>(another)->data);
}
bool VentureAtom::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureAtom>(another)->data);
}
bool VentureSimplexPoint::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureSimplexPoint>(another)->data); // FIXME: is it enough? Check for other Venture data types.
}
bool VentureSmoothedCountVector::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureSmoothedCountVector>(another)->data); // FIXME: is it enough? Check for other Venture data types.
}
bool VentureSmoothedCount::CompareByValue(shared_ptr<VentureValue> another) {
  return (this->data == ToVentureType<VentureSmoothedCount>(another)->data);
}
bool VentureList::CompareByValue(shared_ptr<VentureValue> another) {
  shared_ptr<VentureList> this_list = dynamic_pointer_cast<VentureList>(this->shared_from_this());
  shared_ptr<VentureList> another_list = ToVentureType<VentureList>(another);
  while (this_list != NIL_INSTANCE) {
    if (another_list == NIL_INSTANCE) { return false; } // Different sizes.
    if (GetFirst(this_list)->GetType() != GetFirst(another_list)->GetType()) {
      return false; // Different types.
    }
    if (GetFirst(this_list)->CompareByValue(GetFirst(another_list)) == false) {
      return false; // The current elements are different.
    }
    this_list = GetNext(this_list);
    another_list = GetNext(another_list);
  }
  if (another_list != NIL_INSTANCE) { return false; } // Different sizes.
  return true;
}
// We do not need this function?
// But without this function ToVentureType<VentureLambda>(...)
// would be unresolved?
// Added later: I use it for figuring out if the operator has not changed or not.
bool VentureLambda::CompareByValue(shared_ptr<VentureValue> another) {
  assert(this->expressions.lock() != shared_ptr<NodeEvaluation>());
  assert(ToVentureType<VentureLambda>(another)->expressions.lock() != shared_ptr<NodeEvaluation>());
  // It is enough to compare by expressions: ?
  return (this->expressions.lock() == ToVentureType<VentureLambda>(another)->expressions.lock());
}
// We do not need this function?
// But without this function ToVentureType<VentureLambda>(...)
// would be unresolved?
// Added later: I use it for figuring out if the operator has not changed or not.
bool VentureXRP::CompareByValue(shared_ptr<VentureValue> another) {
  assert(this->xrp != shared_ptr<XRP>());
  assert(ToVentureType<VentureXRP>(another)->xrp != shared_ptr<XRP>());
  // It is enough to compare by expressions: ?
  return (this->xrp == ToVentureType<VentureXRP>(another)->xrp);
}

// *** Functions for list ***
shared_ptr<VentureValue> GetFirst(shared_ptr<VentureList> list) {
  if (list->GetType() == NIL) {
    return list;
  } else {
    return list->car;
  }
}
shared_ptr<VentureList> GetNext(shared_ptr<VentureList> list) {
  if (list->GetType() == NIL) {
    return list;
  } else {
    return list->cdr;
  }
}
shared_ptr<VentureValue> GetNth(shared_ptr<VentureList> list, size_t position) { // Enumeration from "1"!
  for (size_t index = 1; index < position; index++) {
    list = GetNext(list);
  }
  return GetFirst(list);
}
void AddToList(shared_ptr<VentureList> target_list, shared_ptr<VentureValue> element) {
  if (target_list->GetType() == NIL) {
    throw std::runtime_error("Function AddToList should not change NIL_INSTANCE.");
  }
  while (target_list->cdr != NIL_INSTANCE) {
    target_list = GetNext(target_list);
  }
  target_list->cdr = shared_ptr<VentureList>(new VentureList(element));
}
shared_ptr<VentureList> Cons(shared_ptr<VentureValue> car, shared_ptr<VentureList> cdr) {
  return shared_ptr<VentureList>(new VentureList(car, cdr));
}
size_t GetSize(shared_ptr<VentureList> list) {
  size_t size = 0;
  while (list != NIL_INSTANCE) {
    list = GetNext(list);
    size++;
  }
  return size;
}

// *** Different things ***
bool StandardPredicate(shared_ptr<VentureValue> value) {
  if (VerifyVentureType<VentureBoolean>(value) == true &&
        CompareValue(value, shared_ptr<VentureValue>(new VentureBoolean(false)))) {
    return false;
  } else {
    return true;
  }
}

// *** DEPRECATED THINGS FOR WORK WITH VentureTypes ***
void AssertVentureSymbol(shared_ptr<VentureValue> value) {
  if (dynamic_cast<VentureSymbol*>(value.get()) == 0 || value->GetType() != SYMBOL) {
    throw std::runtime_error(string(string("Assertion: it is not a symbol.") + value->GetString() + string(boost::lexical_cast<string>(value->GetType()))).c_str());
  }
}
shared_ptr<VentureSymbol> ToVentureSymbol(shared_ptr<VentureValue> value_reference) {
  AssertVentureSymbol(value_reference);
  shared_ptr<VentureSymbol> return_reference = dynamic_pointer_cast<VentureSymbol>(value_reference);
  return return_reference;
}
void AssertVentureList(shared_ptr<VentureValue> value) {;
  if (dynamic_cast<VentureList*>(value.get()) == 0) { // If dynamic_cast returns NULL.
    throw std::runtime_error(string(string("Assertion: it is not a list.") + value->GetString() + string(boost::lexical_cast<string>(value->GetType()))).c_str());
  }
}
shared_ptr<VentureList> ToVentureList(shared_ptr<VentureValue> value_reference) {
  AssertVentureList(value_reference);
  shared_ptr<VentureList> return_reference = dynamic_pointer_cast<VentureList>(value_reference);
  return return_reference;
}

VenturePythonObject::VenturePythonObject(PyObject* python_object)
  : python_object(python_object)
{
  if (python_object == NULL) {
    throw std::runtime_error("python_objects should not be NULL!");
  }
}

VenturePythonObject::~VenturePythonObject() {
  Py_DECREF(python_object);
}

void VenturePythonObject::CheckMyData(VentureValue* venture_value)
{}

VentureDataTypes VenturePythonObject::GetType() { return PYTHON_OBJECT; }

PyObject* VenturePythonObject::GetAsPythonObject() {
  Py_INCREF(python_object); // We assume that somebody is going to use this object.
  return python_object;
}

bool VenturePythonObject::CompareByValue(shared_ptr<VentureValue> another) {
  // Should be better, with Python "=="!
  return (this->python_object == ToVentureType<VenturePythonObject>(another)->python_object);
}

string VenturePythonObject::GetString() {return "PYTHON_OBJECT_OPAQUE";}

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
  VentureExternalXRPObject::~VentureExternalXRPObject() {
    this->CheckMyData(this);
    if (this->socket == NULL) {
      return;
    }
    
    string message = boost::lexical_cast<string>("DeleteXRPID:") + boost::lexical_cast<string>(this->data); 
    zmq_msg_t request;
    zmq_msg_init_size (&request, message.length());
    memcpy (zmq_msg_data (&request), message.c_str(), message.length());
    zmq_msg_send (&request, this->socket, 0);
    zmq_msg_close (&request);
    
    //Wait for a '0', which indicates success 
    zmq_msg_t reply;
    zmq_msg_init (&reply);
    zmq_msg_recv (&reply, this->socket, 0);
    zmq_msg_close (&reply);
  }

  void VentureExternalXRPObject::CheckMyData(VentureValue* venture_value) {
    if (venture_value->GetInteger() < 0) {
      throw std::runtime_error("VentureExternalXRPObject should be non-negative.");
    }
  }

  VentureExternalXRPObject::VentureExternalXRPObject(const int data, void *socket) : data(data), socket(socket) {
    this->CheckMyData(this);
    this->socket = socket;
  }

  VentureDataTypes VentureExternalXRPObject::GetType() { return EXTERNALXRP; }

  real VentureExternalXRPObject::GetReal(){
    return data;
  }

  int VentureExternalXRPObject::GetInteger() {
    return data;
  }

  PyObject* VentureExternalXRPObject::GetAsPythonObject() { return Py_BuildValue("i", this->data); }

  bool VentureExternalXRPObject::CompareByValue(shared_ptr<VentureValue> another) {
    return (this->data == ToVentureType<VentureExternalXRPObject>(another)->data);
  }

  string VentureExternalXRPObject::GetString() {return boost::lexical_cast<string>(data);}
#endif
