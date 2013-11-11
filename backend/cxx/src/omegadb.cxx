#include "omegadb.h"
#include <cassert>

OmegaDB::~OmegaDB() { assert(isValid()); magic = 0; }
