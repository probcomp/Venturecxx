#ifndef FLUSH_H
#define FLUSH_H

#include <cstdio>
#include "all.h"

struct SPAux;
struct VentureValue;
struct SP;
struct Node;
struct OmegaDB;

enum class NodeType;

// Should have an enum class for the three different types
// flushValue
// flushAux
// flushFamily
struct FlushEntry
{
  FlushEntry(SP * owner, VentureValue * value, NodeType nodeType):
    owner(owner), value(value), nodeType(nodeType) { }

  SP * owner{nullptr};
  
  VentureValue * value{nullptr};
  NodeType nodeType;

};

void destroyFamilyNodes(Node * root);
void flushDB(OmegaDB * omegaDB, bool isActive);


#endif
