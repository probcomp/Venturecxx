#include "../inc/wttree.hpp"

using wttree::PMap;

int main() {
  PMap<int, int> pmap;
  
  for (int i = 0; i < 100; ++i)
  {
    pmap = pmap.insert(i, i);
  }
}
