#include "HeaderPre.h"
#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "Analyzer.h"
#include "XRPCore.h"
#include "RIPL.h"
#include "ERPs.h"
#include "Primitives.h"

real Primitive::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                shared_ptr<VentureValue> sampled_value) { // inline?
  return log(1.0);
}
  
bool Primitive::IsRandomChoice() { return false; }
bool Primitive::CouldBeRescored() { return false; }
string Primitive::GetName() { return "PrimitiveClass"; }


shared_ptr<VentureValue> Primitive__BooleanNot::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if(arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  
  bool result = StandardPredicate(arguments[0]);
  return shared_ptr<VentureValue>(new VentureBoolean(!result));
}
string Primitive__BooleanNot::GetName() { return "Primitive__BooleanNot"; }

shared_ptr<VentureValue> Primitive__RealPlus::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  for (size_t index = 0; index < arguments.size(); index++) {
    result->data += arguments[index]->GetReal();
  }
  return result;
}
string Primitive__RealPlus::GetName() { return "Primitive__RealPlus"; }

shared_ptr<VentureValue> Primitive__RealMultiply::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(1.0));
  for (size_t index = 0; index < arguments.size(); index++) {
    result->data *= arguments[index]->GetReal();
  }
  return result;
}
string Primitive__RealMultiply::GetName() { return "Primitive__RealMultiply"; }

shared_ptr<VentureValue> Primitive__RealPower::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  result->data
    = pow(arguments[0]->GetReal(),
          arguments[1]->GetReal());
  return result;
}
string Primitive__RealPower::GetName() { return "Primitive__RealPower"; }

shared_ptr<VentureValue> Primitive__RealMinus::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  result->data
    = arguments[0]->GetReal() -
        arguments[1]->GetReal();
  return result;
}
string Primitive__RealMinus::GetName() { return "Primitive__RealMinus"; }

shared_ptr<VentureValue> Primitive__RealDivide::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  result->data
    = arguments[0]->GetReal() /
        arguments[1]->GetReal();
  return result;
}
string Primitive__RealDivide::GetName() { return "Primitive__RealDivide"; }

shared_ptr<VentureValue> Primitive__RealCos::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  result->data
    = cos(arguments[0]->GetReal());
  return result;
}
string Primitive__RealCos::GetName() { return "Primitive__RealCos"; }

shared_ptr<VentureValue> Primitive__RealSin::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureReal> result = shared_ptr<VentureReal>(new VentureReal(0.0));
  result->data
    = sin(arguments[0]->GetReal());
  return result;
}
string Primitive__RealSin::GetName() { return "Primitive__RealSin"; }

shared_ptr<VentureValue> Primitive__RealEqualOrGreater::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetReal() >= arguments[1]->GetReal()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__RealEqualOrGreater::GetName() { return "Primitive__RealEqualOrGreater"; }

shared_ptr<VentureValue> Primitive__RealEqualOrLesser::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetReal() <= arguments[1]->GetReal()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__RealEqualOrLesser::GetName() { return "Primitive__RealEqualOrLesser"; }

shared_ptr<VentureValue> Primitive__RealGreater::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetReal() > arguments[1]->GetReal()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__RealGreater::GetName() { return "Primitive__RealGreater"; }

shared_ptr<VentureValue> Primitive__RealLesser::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetReal() < arguments[1]->GetReal()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__RealLesser::GetName() { return "Primitive__RealLesser"; }

shared_ptr<VentureValue> Primitive__RealEqual::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result = fabs(arguments[0]->GetReal() - arguments[1]->GetReal()) < comparison_epsilon;
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__RealEqual::GetName() { return "Primitive__RealEqual"; }

shared_ptr<VentureValue> Primitive__SimplexPoint::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  size_t dimension = arguments.size();
  vector<real> weights(dimension);
    
  for(size_t index = 0; index < dimension; index++) {
    weights[index] = arguments[index]->GetReal();
  }
  
  return shared_ptr<VentureSimplexPoint>(new VentureSimplexPoint(weights));
}
string Primitive__SimplexPoint::GetName() {return "Primitive__SimplexPoint";}

shared_ptr<VentureValue> Primitive__List::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() == 0) {
    return NIL_INSTANCE;
  }
  shared_ptr<VentureList> new_list =
    shared_ptr<VentureList>(new VentureList(arguments[0]));
  for (size_t index = 1; index < arguments.size(); index++) {
    // AddToList() is not efficient!
    AddToList(new_list,
              arguments[index]);
  }
  return new_list;
}
string Primitive__List::GetName() { return "Primitive__List"; }

shared_ptr<VentureValue> Primitive__First::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return GetFirst(ToVentureType<VentureList>(arguments[0]));
}
string Primitive__First::GetName() { return "Primitive__First"; }

shared_ptr<VentureValue> Primitive__Rest::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return GetNext(ToVentureType<VentureList>(arguments[0]));
}
string Primitive__Rest::GetName() { return "Primitive__Rest"; }

shared_ptr<VentureValue> Primitive__Cons::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return Cons(arguments[0], ToVentureType<VentureList>(arguments[1]));
}
string Primitive__Cons::GetName() { return "Primitive__Cons"; }

shared_ptr<VentureValue> Primitive__Length::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return shared_ptr<VentureCount>(new VentureCount(GetSize(ToVentureType<VentureList>(arguments[0]))));
}
string Primitive__Length::GetName() { return "Primitive__Length"; }

shared_ptr<VentureValue> Primitive__EmptyQUESTIONMARK::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(GetSize(ToVentureType<VentureList>(arguments[0])) == 0));
}
string Primitive__EmptyQUESTIONMARK::GetName() { return "Primitive__EmptyQUESTIONMARK"; }

shared_ptr<VentureValue> Primitive__Nth::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  assert(arguments[1]->GetInteger() >= 1);
  assert(arguments[1]->GetInteger() <= GetSize(ToVentureType<VentureList>(arguments[0])));
  return GetNth(ToVentureType<VentureList>(arguments[0]), arguments[1]->GetInteger());
}
string Primitive__Nth::GetName() { return "Primitive__Nth"; }

shared_ptr<VentureValue> Primitive__Inc::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  return shared_ptr<VentureCount>(new VentureCount(arguments[0]->GetInteger() + 1));
}
string Primitive__Inc::GetName() { return "Primitive__Inc"; }

shared_ptr<VentureValue> Primitive__Dec::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  return shared_ptr<VentureCount>(new VentureCount(arguments[0]->GetInteger() - 1));
}
string Primitive__Dec::GetName() { return "Primitive__Dec"; }

shared_ptr<VentureValue> Primitive__Equal::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  return shared_ptr<VentureBoolean>(new VentureBoolean(CompareValue(arguments[0], arguments[1])));
}
string Primitive__Equal::GetName() { return "Primitive__Equal"; }










shared_ptr<VentureValue> Primitive__IntegerPlus::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  shared_ptr<VentureCount> result = shared_ptr<VentureCount>(new VentureCount(0));
  for (size_t index = 0; index < arguments.size(); index++) {
    result->data += arguments[index]->GetInteger();
  }
  return result;
}
string Primitive__IntegerPlus::GetName() { return "Primitive__IntegerPlus"; }

shared_ptr<VentureValue> Primitive__IntegerMultiply::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  shared_ptr<VentureCount> result = shared_ptr<VentureCount>(new VentureCount(1));
  for (size_t index = 0; index < arguments.size(); index++) {
    result->data *= arguments[index]->GetInteger();
  }
  return result;
}
string Primitive__IntegerMultiply::GetName() { return "Primitive__IntegerMultiply"; }

shared_ptr<VentureValue> Primitive__IntegerMinus::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureCount> result = shared_ptr<VentureCount>(new VentureCount(0));
  result->data
    = arguments[0]->GetInteger() -
        arguments[1]->GetInteger();
  return result;
}
string Primitive__IntegerMinus::GetName() { return "Primitive__IntegerMinus"; }

shared_ptr<VentureValue> Primitive__IntegerDivide::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureCount> result = shared_ptr<VentureCount>(new VentureCount(0));
  result->data
    = arguments[0]->GetInteger() /
        arguments[1]->GetInteger();
  return result;
}
string Primitive__IntegerDivide::GetName() { return "Primitive__IntegerDivide"; }




shared_ptr<VentureValue> Primitive__IntegerEqualOrGreater::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetInteger() >= arguments[1]->GetInteger()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__IntegerEqualOrGreater::GetName() { return "Primitive__IntegerEqualOrGreater"; }

shared_ptr<VentureValue> Primitive__IntegerEqualOrLesser::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetInteger() <= arguments[1]->GetInteger()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__IntegerEqualOrLesser::GetName() { return "Primitive__IntegerEqualOrLesser"; }

shared_ptr<VentureValue> Primitive__IntegerGreater::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetInteger() > arguments[1]->GetInteger()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__IntegerGreater::GetName() { return "Primitive__IntegerGreater"; }

shared_ptr<VentureValue> Primitive__IntegerLesser::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetInteger() < arguments[1]->GetInteger()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__IntegerLesser::GetName() { return "Primitive__IntegerLesser"; }

shared_ptr<VentureValue> Primitive__IntegerEqual::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }

  bool result;
  if (arguments[0]->GetInteger() == arguments[1]->GetInteger()) {
    result = true;
  } else {
    result = false;
  }
  return shared_ptr<VentureBoolean>(new VentureBoolean(result));
}
string Primitive__IntegerEqual::GetName() { return "Primitive__IntegerEqual"; }

shared_ptr<VentureValue> Primitive__IntegerModulo::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  shared_ptr<VentureCount> result = shared_ptr<VentureCount>(new VentureCount(0));
  result->data
    = arguments[0]->GetInteger() %
        arguments[1]->GetInteger();
  return result;
}
string Primitive__IntegerModulo::GetName() { return "Primitive__IntegerModulo"; }

shared_ptr<VentureValue> Primitive__IntegerLeftShift::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = arguments[0]->GetInteger() << arguments[1]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerLeftShift::GetName() { return "Primitive__IntegerLeftShift"; }

shared_ptr<VentureValue> Primitive__IntegerRightShift::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = arguments[0]->GetInteger() >> arguments[1]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerRightShift::GetName() { return "Primitive__IntegerRightShift"; }

shared_ptr<VentureValue> Primitive__IntegerAnd::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = arguments[0]->GetInteger() & arguments[1]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerAnd::GetName() { return "Primitive__IntegerAnd"; }

shared_ptr<VentureValue> Primitive__IntegerOr::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = arguments[0]->GetInteger() | arguments[1]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerOr::GetName() { return "Primitive__IntegerOr"; }

shared_ptr<VentureValue> Primitive__IntegerXor::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = arguments[0]->GetInteger() ^ arguments[1]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerXor::GetName() { return "Primitive__IntegerXor"; }

shared_ptr<VentureValue> Primitive__IntegerNot::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  int result = ~arguments[0]->GetInteger();
  return shared_ptr<VentureCount>(new VentureCount(result));
}
string Primitive__IntegerNot::GetName() { return "Primitive__IntegerNot"; }


shared_ptr<VentureValue> Primitive_LoadPythonShellModule::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  PyRun_SimpleString("import Shell");
  return shared_ptr<VentureBoolean>(new VentureBoolean(true));
}
string Primitive_LoadPythonShellModule::GetName() { return "Primitive_LoadPythonShellModule"; }



shared_ptr<VentureValue> Primitive__SCVPlusSCV::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  if (ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size() != ToVentureType<VentureSmoothedCountVector>(arguments[1])->data.size()) {
    throw std::runtime_error("Smoothed count vectors should have the same size.");
  }
  vector<real> new_vector_elements(ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size());
  for (size_t index = 0; index < ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size(); index++) {
    new_vector_elements[index] =
      ToVentureType<VentureSmoothedCountVector>(arguments[0])->data[index] +
        ToVentureType<VentureSmoothedCountVector>(arguments[1])->data[index];
  }
  return shared_ptr<VentureSmoothedCountVector>(new VentureSmoothedCountVector(new_vector_elements));
}
string Primitive__SCVPlusSCV::GetName() { return "Primitive__SCVPlusSCV"; }

shared_ptr<VentureValue> Primitive__SCVMultiplyScalar::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  vector<real> new_vector_elements(ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size());
  for (size_t index = 0; index < ToVentureType<VentureSmoothedCountVector>(arguments[0])->data.size(); index++) {
    new_vector_elements[index] =
      ToVentureType<VentureSmoothedCountVector>(arguments[0])->data[index] *
        arguments[1]->GetReal();
  }
  return shared_ptr<VentureSmoothedCountVector>(new VentureSmoothedCountVector(new_vector_elements));
}
string Primitive__SCVMultiplyScalar::GetName() { return "Primitive__SCVMultiplyScalar"; }

shared_ptr<VentureValue> Primitive__SCV::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 1) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  // Write a better error if argument is not a simplex point! Support more types?
  vector<real> new_vector_elements(ToVentureType<VentureSimplexPoint>(arguments[0])->data.size());
  for (size_t index = 0; index < new_vector_elements.size(); index++) {
    new_vector_elements[index] = ToVentureType<VentureSimplexPoint>(arguments[0])->data[index];
  }
  return shared_ptr<VentureSmoothedCountVector>(new VentureSmoothedCountVector(new_vector_elements));
}
string Primitive__SCV::GetName() { return "Primitive__SCV"; }

shared_ptr<VentureValue> Primitive__RepeatSCV::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  if (arguments.size() != 2) {
    throw std::runtime_error("Wrong number of arguments.");
  }
  // Not efficient, make with vector(..., ...)!
  vector<real> new_vector_elements(arguments[1]->GetInteger());
  for (size_t index = 0; index < arguments[1]->GetInteger(); index++) {
    new_vector_elements[index] = arguments[0]->GetReal();
  }
  return shared_ptr<VentureSmoothedCountVector>(new VentureSmoothedCountVector(new_vector_elements));
}
string Primitive__RepeatSCV::GetName() { return "Primitive__RepeatSCV"; }





shared_ptr<VentureValue> Primitive__LoadPythonFunction::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config)
{
  shared_ptr<XRP> new_function = shared_ptr<XRP>(new ERP__PythonFunctionTemplate());
  dynamic_pointer_cast<ERP__PythonFunctionTemplate>(new_function)->module_name = arguments[0]->GetString();
  dynamic_pointer_cast<ERP__PythonFunctionTemplate>(new_function)->function_name = arguments[1]->GetString();
  dynamic_pointer_cast<ERP__PythonFunctionTemplate>(new_function)->if_stochastic = ToVentureType<VentureBoolean>(arguments[2])->data;
  return shared_ptr<VentureXRP>(new VentureXRP(new_function));
}
string Primitive__LoadPythonFunction::GetName() {
  return "Primitive__LoadPythonFunction";
}

#include "PythonProxy.h"

real ERP__PythonFunctionTemplate::GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >& arguments,
                                 shared_ptr<VentureValue> sampled_value)
{
  if (this->if_stochastic == true) {
    vector< shared_ptr<VentureValue> > new_arguments = arguments;
    new_arguments.push_back(sampled_value);
    return PyFloat_AsDouble(ExecutePythonFunction(this->module_name, this->function_name + "_logscore", new_arguments)->GetAsPythonObject());
  } else {
    return log(1.0);
  }
}
shared_ptr<VentureValue> ERP__PythonFunctionTemplate::Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config) {
  vector< shared_ptr<VentureValue> > new_arguments = arguments;
  new_arguments.insert(new_arguments.begin(), shared_ptr<VentureString>(new VentureString(this->function_name)));
  return ExecutePythonFunction(this->module_name, this->function_name, arguments);
}
string ERP__PythonFunctionTemplate::GetName() {
  return "ERP__PythonFunctionTemplate";
}
