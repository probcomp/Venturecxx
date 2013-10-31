#ifndef ENV_H
#define ENV_H

#include <string>
#include <unordered_map>
#include "address.h"

struct Environment
{
  /* For empty environment. */
  Environment(const Address & outerEnvAddr): outerEnvAddr(outerEnvAddr) {}

  void addBinding(std::string s, Address address) { frame[s] = address; }

  std::unordered_map<std::string, Address> frame;
  Address outerEnvAddr;
};

#endif
