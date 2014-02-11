PyTrace::PyTrace() { throw 500; }
PyTrace::~PyTrace() { throw 500; }
  
void PyTrace::evalExpression(DirectiveID did, boost::python::object object) 
{
  VentureValuePtr exp = parseExpression(o);
  pair<double,Node*> p = evalFamily(trace,exp,globalEnv,Scaffold(),DB(),NULL);
  assert(p.first == 0);
  assert(!trace->families.count(did));
  trace->families[did] = p.second;
}

void PyTrace::unevalDirectiveID(DirectiveID did) 
{ 
  assert(trace->families.count(did));
  unevalFamily(trace,trace->families[did],new Scaffold(),new DB());
  trace->families.erase(did);
}

void PyTrace::observe(DirectiveID did,boost::python::object valueExp)
{
  assert(trace->families.count(did));
  Node * node = trace->families[did];
  trace->unpropagatedObservations[node] = parseValue(valueExp);
}

void PyTrace::unobserve(size_t directiveID)
{
  assert(trace->families.count(did));
  Node * node = trace->families[id];
  OutputNode * appNode = trace->getOutermostNonReferenceApplication(node);
  if (trace->isObservation(node)) { unconstrain(trace,appNode); }
  else
  {
    assert(trace->unpropagatedObservations.count(node));
    trace->unpropagatedObservations.erase(node);
  }
}

void PyTrace::bindInGlobalEnv(string sym, DirectiveID did)
{
  trace->globalEnv->addBinding(new VentureSymbol(sym),trace->families[did]);
}

boost::python::object PyTrace::extractPythonValue(DirectiveID did)
{
  assert(trace->families.count(did));
  Node * node = trace->families[did];
  VentureValuePtr value = trace->getValue(node);
  assert(value.get());
  return value->toPython();
}

void PyTrace::setSeed(size_t n) {
  gsl_rng_set(trace->rng, n);
}

size_t PyTrace::getSeed() {
  // TODO FIXME get_seed can't be implemented as spec'd (need a generic RNG state); current impl always returns 0, which may not interact well with VentureUnit
  return 0;
}


double PyTrace::getGlobalLogScore() 
{
  double ls = 0.0;
  for (size_t i = 0; i < trace->unconstrainedRandomChoices.size(); ++i)
  {
    Node * node = trace->unconstrainedRandomChoices[i];
    ls += trace->getPSP(node)->logDensity(trace->getValue(node),node);
  }
  for (size_t i = 0; i < trace->constrainedRandomChoices.size(); ++i)
  {
    Node * node = trace->constrainedRandomChoices[i];
    ls += trace->getPSP(node)->logDensity(trace->getValue(node),node);
  }
  return ls;
}

uint32_t PyTrace::numRandomChoices() { return trace->numRandomChoices(); }

void PyTrace::infer(boost::python::dict params) { throw "INFER not yet implemented"; }
