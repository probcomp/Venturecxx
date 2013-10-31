#include "node.h"
#include "spaux.h"
#include "value.h"
#include "value_types.h"
#include "sps/csp.h"
#include <string>
#include <vector>


VentureValue * CSP::simulateRequest(Node * node, gsl_rng * rng)
{
  std::string name = std::to_string(std::hash<std::string>()(node->address.toString()));
  Environment env(envAddr);
  for (size_t i = 0; i < ids.size(); ++i)
    {
      env.addBinding(ids[i],node->operandNodes[i]->address);
    }
  CSR csr(name,body,env);
  return new VentureRequest({csr});
}
