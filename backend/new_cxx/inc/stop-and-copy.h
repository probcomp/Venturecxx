#ifndef STOP_AND_COPY_H
#define STOP_AND_COPY_H

struct ForwardingMap
{
  map<void*, void*> pointers;
  size_t count(void* k) const;
  void*& operator[] (void* k);
};

#endif
