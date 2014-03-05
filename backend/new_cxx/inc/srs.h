#ifndef SRS_H
#define SRS_H

#include "types.h"

struct VentureEnvironment;

struct ESR
{
  ESR(FamilyID id,VentureValuePtr exp,shared_ptr<VentureEnvironment> env) :
    id(id), exp(exp), env(env) {};
  FamilyID id;
  VentureValuePtr exp;
  shared_ptr<VentureEnvironment> env;
};

struct LSR { virtual ~LSR() {} };


#endif
