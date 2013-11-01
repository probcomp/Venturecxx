#ifndef SRS_H
#define SRS_H

#include "exp.h"
#include "env.h"

#include <string>

/* Exposed simulation request */
struct ESR
{
  ESR(size_t id, Expression exp, Environment env): id(id), exp(exp), env(env) {}

  size_t id;
  Expression exp;
  Environment env;
};

/* Hidden simulation request */
struct HSR { virtual ~HSR() {} } ;

#endif
