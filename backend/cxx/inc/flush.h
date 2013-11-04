#ifndef FLUSH_H
#define FLUSH_H

struct Node;
struct OmegaDB;

void destroyFamilyNodes(Node * root);
void flushDB(OmegaDB * omegaDB, bool isActive);


#endif
