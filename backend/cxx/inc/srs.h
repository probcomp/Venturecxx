#ifndef SRS_H
#define SRS_H

#include "exp.h"
#include "env.h"

#include <string>

struct CSR
{
  CSR(std::string name, Expression exp, Environment env):
    name(name), exp(exp), env(env) {}

  std::string name;
  Expression exp;
  Environment env;
};

struct ESR {} ;

#endif
