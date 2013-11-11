
#ifndef VENTURE___PRIMITIVES_H
#define VENTURE___PRIMITIVES_H

#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "XRPCore.h"
#include "ERPs.h"

class Primitive : public ERP {
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value);
  
public:
  virtual bool IsRandomChoice();
  virtual bool CouldBeRescored();
  virtual string GetName();
};

class Primitive__BooleanNot : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealPlus : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealMultiply : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealPower : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealMinus : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealDivide : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealCos : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealSin : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealEqualOrGreater : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealEqualOrLesser : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealGreater : public Primitive { // Useless for Real?
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealLesser : public Primitive { // Useless for Real?
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RealEqual : public Primitive { // With epsilon.
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

// Constructs a VentureSimplexPoint, arguments should support GetReal().
class Primitive__SimplexPoint : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__List : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__First : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Rest : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Length : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__EmptyQUESTIONMARK : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Cons : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Nth : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Inc : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Dec : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__Equal : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};





class Primitive__IntegerPlus : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerMultiply : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerMinus : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerDivide : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerEqualOrGreater : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerEqualOrLesser : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerGreater : public Primitive { // Useless for Integer?
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerLesser : public Primitive { // Useless for Integer?
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerEqual : public Primitive { // With epsilon.
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerModulo : public Primitive { // With epsilon.
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

//bitwise operations

class Primitive__IntegerLeftShift : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerRightShift : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerAnd : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerOr : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerXor : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__IntegerNot : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};


class Primitive__SCVPlusSCV : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__SCVMultiplyScalar : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__SCV : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class Primitive__RepeatSCV : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};



class Primitive_LoadPythonShellModule : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};



class Primitive__LoadPythonFunction : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
public:
  virtual string GetName();
};

class ERP__PythonFunctionTemplate : public ERP {
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value);
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);

public:
  string module_name;
  string function_name;
  bool if_stochastic;

  virtual string GetName();
};

#endif
