#ifndef SP_RECORD_H
#define SP_RECORD_H

#include "types.h"

struct SPFamilies;
struct SPAux;
struct VentureSP;

// TODO URGENT not sure when or how this is called yet.
struct SPRecord
{
  shared_ptr<SPFamilies> spFamilies;
  shared_ptr<SPAux> spAux;
  shared_ptr<VentureSP> sp;
};


#endif
