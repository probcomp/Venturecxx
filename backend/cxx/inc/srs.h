#ifndef SRS_H
#define SRS_H

struct VentureEnvironment;

struct ESR
{
  ESR(FamilyID id,VentureValuePtr exp,shared_ptr<VentureEnvironment> env);
  FamilyID id;
  VentureValuePtr exp;
  shared_ptr<VentureEnvironment> env;
};

struct LSR { virtual ~LSR() {} };


#endif
