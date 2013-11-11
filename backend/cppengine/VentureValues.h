#ifndef VENTURE___VENTURE_VALUES_H
#define VENTURE___VENTURE_VALUES_H

#include "Header.h"

enum VentureDataTypes
{
  UNDEFINED_TYPE, BOOLEAN, COUNT, REAL, PROBABILITY, ATOM, SIMPLEXPOINT, SMOOTHEDCOUNT, NIL, LIST, SYMBOL, LAMBDA, XRP_REFERENCE, NODE, PYTHON_OBJECT,
  SMOOTHED_COUNT_VECTOR, STRING

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
  , ZMQ, EXTERNALXRP
#endif

};

struct VentureValue : public boost::enable_shared_from_this<VentureValue> {
  VentureValue();
  static void CheckMyData(VentureValue* venture_value);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual int GetInteger();
  virtual PyObject* GetAsPythonObject();
  ~VentureValue();
};

template <typename T>
bool VerifyVentureType(shared_ptr<VentureValue>);

template <typename T>
void AssertVentureType(shared_ptr<VentureValue>);

template <typename T>
shared_ptr<T> ToVentureType(shared_ptr<VentureValue>);

struct VentureBoolean : public VentureValue {
  VentureBoolean(const bool);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal(); // Should be deleted!
  virtual int GetInteger();
  virtual PyObject* GetAsPythonObject();
  ~VentureBoolean();

  bool data;
};

struct VentureCount : public VentureValue {
  VentureCount(const int);
  //VentureCount(const string&);
  static void CheckMyData(VentureValue* venture_value);
  // Question: where would be the type transformation happen?
  //           Before this function, it seems?
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual int GetInteger();
  virtual PyObject* GetAsPythonObject();
  ~VentureCount();

  int data;
};

struct VentureReal : public VentureValue {
  VentureReal(const real);
  static void CheckMyData(VentureValue* venture_value);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual PyObject* GetAsPythonObject();
  ~VentureReal();

  real data;
};

struct VentureProbability : public VentureValue {
  VentureProbability(const real);
  static void CheckMyData(VentureValue* venture_value);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual PyObject* GetAsPythonObject();
  ~VentureProbability();

  real data;
};

struct VentureAtom : public VentureValue {
  VentureAtom(const int);
  static void CheckMyData(VentureValue* venture_value);
  // Question: where would be the type transformation happen?
  //           Before this function, it seems?
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual int GetInteger();
  virtual PyObject* GetAsPythonObject();
  ~VentureAtom();

  int data;
};

struct VentureSimplexPoint : public VentureValue {
  VentureSimplexPoint(vector<real>&);
  static void CheckMyData(VentureValue* venture_value);
  // Question: where would be the type transformation happen?
  //           Before this function, it seems?
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureSimplexPoint();

  vector<real> data;
};

struct VentureSmoothedCount : public VentureValue {
  VentureSmoothedCount(const real);
  static void CheckMyData(VentureValue* venture_value);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual real GetReal();
  virtual PyObject* GetAsPythonObject();
  ~VentureSmoothedCount();

  real data;
};

struct VentureSmoothedCountVector : public VentureValue {
  VentureSmoothedCountVector(vector<real>&);
  static void CheckMyData(VentureValue* venture_value);
  // Question: where would be the type transformation happen?
  //           Before this function, it seems?
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureSmoothedCountVector();

  vector<real> data;
};

struct VentureList;

extern shared_ptr<VentureList> const NIL_INSTANCE;

// Should be references constants?
// Should be renamed to the VentureCons!
struct VentureList : public VentureValue {
  VentureList(shared_ptr<VentureValue> car);
  VentureList(shared_ptr<VentureValue> car, shared_ptr<VentureList> cdr);
  virtual VentureDataTypes GetType(); // Should be virtual for NIL?..
  // FIXME: add CompareByValue? Do not forget about the NIL, that it has another type?
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureList();

  shared_ptr<VentureValue> car;
  shared_ptr<VentureList> cdr;
};

struct VentureNil : public VentureList {
  VentureNil();
  virtual VentureDataTypes GetType();
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureNil();
};

// http://stackoverflow.com/questions/2926878/determine-if-a-string-contains-only-alphanumeric-characters-or-a-space
bool is_not_legal_SYMBOL_character(char); // static inline?
bool legal_SYMBOL_name(const string&); // static inline?

// Where is the check implemented?
struct VentureSymbol : public VentureValue {
  VentureSymbol(const string&);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureSymbol();

  string symbol;
};

struct NodeEvaluation;
struct NodeEnvironment;
class XRP;

struct VentureLambda : public VentureValue {
  VentureLambda(shared_ptr<VentureList>,
                shared_ptr<NodeEvaluation>,
                shared_ptr<NodeEnvironment>);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>); // We really do not need this function?
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureLambda();

  shared_ptr<VentureList> formal_arguments;
  weak_ptr<NodeEvaluation> expressions;
  weak_ptr<NodeEnvironment> scope_environment;
};

struct VentureXRP : public VentureValue {
  VentureXRP(shared_ptr<XRP>);
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>); // We really do not need this function?
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VentureXRP();

  shared_ptr<XRP> xrp;
};

void AssertVentureSymbol(shared_ptr<VentureValue>);

shared_ptr<VentureSymbol> ToVentureSymbol(shared_ptr<VentureValue>);

void AssertVentureList(shared_ptr<VentureValue>);

shared_ptr<VentureList> ToVentureList(shared_ptr<VentureValue>);

shared_ptr<VentureValue> GetFirst(shared_ptr<VentureList>);

shared_ptr<VentureList> GetNext(shared_ptr<VentureList>);

shared_ptr<VentureValue> GetNth(shared_ptr<VentureList>, size_t);

void AddToList(shared_ptr<VentureList>, shared_ptr<VentureValue>);

shared_ptr<VentureList> Cons(shared_ptr<VentureValue>, shared_ptr<VentureList>);

size_t GetSize(shared_ptr<VentureList> list);

bool StandardPredicate(shared_ptr<VentureValue>);

struct VenturePythonObject : public VentureValue {
  VenturePythonObject(PyObject* python_object);
  static void CheckMyData(VentureValue* venture_value);
  // Question: where would be the type transformation happen?
  //           Before this function, it seems?
  virtual VentureDataTypes GetType();
  virtual bool CompareByValue(shared_ptr<VentureValue>);
  virtual string GetString();
  virtual PyObject* GetAsPythonObject();
  ~VenturePythonObject();

  PyObject* python_object;
};
  
// TMP.
struct VentureString : public VentureValue {
  VentureString(string data) : data(data) {}
  virtual VentureDataTypes GetType() { return STRING; }
  virtual bool CompareByValue(shared_ptr<VentureValue> another) {
    return ToVentureType<VentureString>(another)->data == data;
  } // We really do not need this function?
  virtual string GetString() { return data; }
  virtual PyObject* GetAsPythonObject() { return Py_BuildValue("s", data.c_str()); }

  string data;
};

#ifdef VENTURE__FLAG__COMPILE_WITH_ZMQ
  struct VentureExternalXRPObject : public VentureValue {
    VentureExternalXRPObject(const int, void *);
    static void CheckMyData(VentureValue* venture_value);
    // Question: where would be the type transformation happen?
    //           Before this function, it seems?
    virtual VentureDataTypes GetType();
    virtual bool CompareByValue(shared_ptr<VentureValue>);
    virtual string GetString();
    virtual real GetReal();
    virtual int GetInteger();
    virtual PyObject* GetAsPythonObject();
    ~VentureExternalXRPObject();

    int data;
    void *socket;
  };
#endif

#endif
