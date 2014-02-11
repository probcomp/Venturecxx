#ifndef LKERNEL_H
#define LKERNEL_H

struct LKernel
{
  virtual VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,Args * args) =0;
  virtual double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,Args * args) { return 0; }
  virtual double reverseWeight(Trace * trace,VentureValuePtr oldValue,Args * args) 
    { 
      return weight(trace,oldValue,shared_ptr<VentureValue>(nullptr),args);
    }
  virtual bool isIndependent() const { return true; }
};

struct DefaultAAAKernel : LKernel
{
  DefaultAAAKernel(const VentureSPPtr makerSP): makerSP(makerSP) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,Args * args) override;
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,Args * args) override;

  const VentureSPPtr makerSP;

};

struct DeterministicLKernel : LKernel
{
  DeterministicLKernel(VentureValuePtr value, VentureSPPtr sp): value(value), sp(sp) {}

  VentureValuePtr simulate(Trace * trace,VentureValuePtr oldValue,Args * args) override;
  double weight(Trace * trace,VentureValuePtr newValue,VentureValuePtr oldValue,Args * args) override;

  VentureValuePtr value;
  VentureSPPtr sp;
  
};





#endif
