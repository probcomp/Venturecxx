
PyTrace::PyTrace() { throw 500; }
PyTrace::~PyTrace() { throw 500; }
  
void PyTrace::evalExpression(size_t did, boost::python::object object) { throw 500; }
void PyTrace::unevalDirectiveID(size_t directiveID) { throw 500; }

void PyTrace::observe(size_t did,boost::python::object valueExp) { throw 500; }
void PyTrace::unobserve(size_t directiveID) { throw 500; }

void PyTrace::bindInGlobalEnv(string sym, size_t did) { throw 500; }

boost::python::object PyTrace::extractPythonValue(size_t did) { throw 500; }

void PyTrace::setSeed(size_t seed) { throw 500; }
size_t PyTrace::getSeed() { throw 500; }

double PyTrace::getGlobalLogScore() { throw 500; }
uint32_t PyTrace::numRandomChoices() { throw 500; }

void PyTrace::infer(boost::python::dict params) { throw 500; }
