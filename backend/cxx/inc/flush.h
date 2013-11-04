#ifndef FLUSH_H
#define FLUSH_H

struct VentureValue;
struct SP;
struct Node;
struct OmegaDB;

enum class NodeType;

enum class FlushType { CONSTANT, REQUEST, OUTPUT, FAMILY_VALUE };

struct FlushEntry
{
  FlushEntry(SP * owner, VentureValue * value, FlushType flushType):
    owner(owner), value(value), flushType(flushType) { }
  SP * owner;
  VentureValue * value;
  FlushType flushType;
};

FlushType nodeTypeToFlushType(NodeType nodeType);

void destroyFamilyNodes(Node * root);
void flushDB(OmegaDB * omegaDB, bool isActive);


#endif
