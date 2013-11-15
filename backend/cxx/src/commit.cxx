#include "node.h"
#include "value.h"
#include "env.h"
#include "sp.h"
#include "trace.h"
#include "sps/csp.h"
#include "scaffold.h"
#include "omegadb.h"
#include "srs.h"
#include "flush.h"
#include "lkernel.h"
#include "utils.h"
#include <cmath>

#include <iostream>
#include <typeinfo>
#include "sps/mem.h"

void Trace::commit(Particle * omega)
{
  
