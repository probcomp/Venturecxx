VentureValuePtr parseValue(boost::python::dict d)
{
  if (d["type"] == "boolean") { return new VentureBool(boost::python::extract<bool>(d["value"])); }
  else if (d["type"] == "number") { return new VentureNumber(boost::python::extract<double>(d["value"])); }
  else if (d["type"] == "symbol") { return new VentureSymbol(boost::python::extract<string>(d["value"])); }
  else if (d["type"] == "atom") { return new VentureAtom(boost::python::extract<uint32_t>(d["value"])); }
  else { assert(false); }
}


VentureValuePtr parseExpression(boost::python::object o)
{
  boost::python::extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return parseValue(getDict()); }
  
  boost::python::extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
  
  vector<VentureValuePtr> exp;
  
  boost::python::ssize_t L = boost::python::len(l);
  
  for(boost::python::ssize_t i=0; i<L; i++)
  {
    exp.push_back(parseExpression(l[i-1]));
  }
  return new VentureArray(exp);
}
