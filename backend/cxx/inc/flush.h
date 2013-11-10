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

  FlushEntry(SP * owner, SPAux * spaux, size_t id):
    owner(owner), spaux(spaux), id(id) { }

  FlushEntry(SP * owner, SPAux * spaux): 
    owner(owner), spaux(spaux), flushAux(true) { }

  SP * owner{nullptr};
  
  VentureValue * value{nullptr};
  NodeType nodeType;

  // TODO could be a type hierarchy
  SPAux * spaux{nullptr}; // ditto
  size_t id{0}; // for flushing families
  bool flushAux{false};

};

void destroyFamilyNodes(Node * root);
void flushDB(OmegaDB * omegaDB, bool isActive);


#endif
