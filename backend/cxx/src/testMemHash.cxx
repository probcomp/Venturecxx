#include "sps/mem.h"
#include <cstdint>
#include <set>
#include <cassert>
#include <boost/functional/hash.hpp>

using std::set;

size_t hashValues(vector<double> elems)
{
  size_t seed = 0;

  for (uint32_t elem : elems) 
  { 
    boost::hash_combine(seed, std::hash<double>()(elem));
  }
  return seed;
}


int main()
{
  uint32_t A,B;

  A = 5000;
  B = 5000;

  map<size_t,pair<double,double> > ids;
  for (uint32_t a = 0; a < A; ++a)
  {
    for (uint32_t b = 0; b < B; ++b)
    {
      vector<double> vals;
      vals.push_back(a);
      vals.push_back(b);
      
      size_t id = hashValues(vals);
      if (ids.count(id))
      {
	cout << "Hash Collision: (" << a << ", " << b << ")";
	cout << " and (" << ids[id].first << ", " << ids[id].second << ")" << endl;
      }
      assert(!ids.count(id));
      ids[id] = make_pair(a,b);
    }
  }
  return 0;
}
