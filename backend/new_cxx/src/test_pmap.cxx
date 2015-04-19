// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

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
