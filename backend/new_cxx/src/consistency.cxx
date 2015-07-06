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

#include "consistency.h"
#include "scaffold.h"
#include "trace.h"

void assertTorus(boost::shared_ptr<Scaffold> scaffold)
{
  for (map<Node*,int>::iterator iter = scaffold->regenCounts.begin();
       iter != scaffold->regenCounts.end();
       ++iter)
  {
    assert(iter->second == 0);
  }
}

void assertTrace(Trace * trace,boost::shared_ptr<Scaffold> scaffold)
{
  for (map<Node*,int>::iterator iter = scaffold->regenCounts.begin();
       iter != scaffold->regenCounts.end();
       ++iter)
  {
    assert(iter->second > 0);
  }
}
