#include "../inc/pmap.hpp"
#include "../inc/pset.hpp"

#include<iostream>

using namespace std;

using persistent::PMap;

int main() {
  PMap<int, int> pmap;
  
  size_t N = 100000;
  
  for (size_t i = 0; i < N; ++i)
  {
    pmap = pmap.insert(i, i);
  }
  
  for(size_t i = N; --i >0;)
  {
    //cout << pmap.size() << endl;
    assert(pmap.contains(i));
    pmap = pmap.remove(i);
    assert(!pmap.contains(i));    
  }
}
