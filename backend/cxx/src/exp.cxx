#include "exp.h"
#include <cassert>

vector<string> Expression::getIDs()
{
  assert(expType == ExpType::LAMBDA);
  vector<string> ids;
  for (Expression exp : exps[1].exps)
  {
    assert(exp.expType == ExpType::VARIABLE);
    ids.push_back(exp.sym);
  }
  return ids;
}
