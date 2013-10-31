#ifndef OMEGA_DB_H
#define OMEGA_DB_H

#include "address.h"
#include "node.h"
#include "value.h"

#include <unordered_map>

struct LatentDB 
{
  virtual ~LatentDB() =0;
};

struct OmegaDB
{
  std::unordered_map<Address, VentureValue *> rcs;
  std::unordered_map<Node *,LatentDB *> latentDBsbyNode;
  std::unordered_map<SP *,LatentDB *> latentDBsbySP;
};


#endif
