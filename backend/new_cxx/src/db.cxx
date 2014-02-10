bool DB::hasValue(Node * node) { throw 500; }
VentureValuePtr DB::registerValue(Node * node) { throw 500; }
void DB::extractValue(Node * node, VentureValuePtr value) { throw 500; }
bool DB::hasLatentDB(Node * node) { throw 500; }
void DB::registerLatentDB(Node * node, VentureValuePtr value) { throw 500; }
Node * DB::getESRParent(VentureSPPtr sp,FamilyID id) { throw 500; }
void DB::registerSPFamily(VentureSPPtr sp,FamilyID id,Node * esrParent) { throw 500; }
