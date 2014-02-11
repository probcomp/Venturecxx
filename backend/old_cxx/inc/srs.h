#ifndef SRS_H
#define SRS_H

#include <string>

struct VentureValue;
struct VentureEnvironment;

/* Exposed simulation request */
struct ESR
{
  ESR(size_t id, VentureValue * exp, VentureEnvironment * env): id(id), exp(exp), env(env) {}

  size_t id;
  VentureValue * exp;
  VentureEnvironment * env;
};

/* Hidden simulation request */
struct HSR { virtual ~HSR() {} } ;

#endif
