#ifndef CONSISTENCY_H
#define CONSISTENCY_H

#include "types.h"

struct Scaffold;
struct Trace;

void assertTorus(shared_ptr<Scaffold> scaffold);
void assertTrace(Trace * trace,shared_ptr<Scaffold> scaffold);



#endif
