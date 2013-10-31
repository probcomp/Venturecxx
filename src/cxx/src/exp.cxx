#include "exp.h"
#include <cassert>

std::vector<std::string> Expression::getIDs()
{
  assert(expType == ExpType::LAMBDA);
  std::vector<std::string> ids;
  for (Expression exp : exps[1].exps)
  {
    assert(exp.expType == ExpType::VARIABLE);
    ids.push_back(exp.sym);
  }
  return ids;
}
