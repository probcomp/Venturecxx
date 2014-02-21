#include "../inc/pmap.hpp"
#include "../inc/pset.hpp"

#include<iostream>

using namespace std;

using persistent::PMap;

int main() {
  PMap<int, int> pmap;
  
  int N = 100000;
  
  for (int i = 0; i < N; ++i)
  {
    pmap = pmap.insert(i, i);
  }
  
  for(int i = N; --i >= 0;)
  {
    //cout << pmap.size() << endl;
    assert(pmap.contains(i));
    assert(pmap.lookup(i) == i);
    pmap = pmap.remove(i);
    assert(!pmap.contains(i));    
  }
  
  assert(pmap.size() == 0);
}
