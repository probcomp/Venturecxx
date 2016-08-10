// Copyright (c) 2014, 2016 MIT Probabilistic Computing Project.
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

#ifndef STOP_AND_COPY_H
#define STOP_AND_COPY_H

struct ForwardingMap
{
  map<const void*, void*> pointers;
  map<const void*, shared_ptr<void> > shared_ptrs;
  size_t count(const void* k) const;
  void*& operator[] (const void* const k);
};

template <typename T>
boost::shared_ptr<T> copy_shared(const boost::shared_ptr<T>& v, ForwardingMap* forward);

#endif
