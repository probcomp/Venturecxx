#ifndef VENTURE___EXTERNAL_XRP_INTERFACE_H
#define VENTURE___EXTERNAL_XRP_INTERFACE_H


#include "Header.h"
#include "VentureValues.h"
#include "VentureParser.h"
#include "XRPCore.h"
#include "ERPs.h"
#include "Primitives.h"


class Primitive__LoadRemoteXRP : public Primitive {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
  virtual void Unsampler(vector< shared_ptr<VentureValue> >& old_arguments, weak_ptr<NodeXRPApplication> caller, shared_ptr<VentureValue> sampled_value);
public:
  virtual string GetName();
};


class XRP__TemplateForExtendedXRP : public XRP {
  virtual shared_ptr<VentureValue> Sampler(vector< shared_ptr<VentureValue> >& arguments, shared_ptr<NodeXRPApplication> caller, EvaluationConfig& evaluation_config);
  virtual real GetSampledLoglikelihood(vector< shared_ptr<VentureValue> >&,
                                       shared_ptr<VentureValue>);
  virtual void Incorporate(vector< shared_ptr<VentureValue> >&,
                                shared_ptr<VentureValue>);
  virtual void Remove(vector< shared_ptr<VentureValue> >&,
                           shared_ptr<VentureValue>);

public:
  virtual bool IsRandomChoice();
  virtual bool CouldBeRescored();
  virtual string GetName();
  bool is_scorable; //true or false from remote XRP
  bool is_random_choice; // true or false from remote XRP
  string name; // change to string later
  void *socket;
  int id_of_this_xrp;
};


#endif