#ifndef MIX_MH_H
#define MIX_MH_H

#include "types.h"
struct ConcreteTrace;
struct ScaffoldIndexer;
struct GKernel;

void mixMH(ConcreteTrace * trace,
	   shared_ptr<ScaffoldIndexer> indexer,
	   shared_ptr<GKernel> gKernel);

#endif
