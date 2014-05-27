#ifndef STOP_AND_COPY_H
#define STOP_AND_COPY_H

struct ForwardingMap
{
  map<const void*, void*> pointers;
  map<const void*, shared_ptr<void> > shared_ptrs;
  size_t count(const void* k) const;
  void*& operator[] (const void* k);
};

#endif
