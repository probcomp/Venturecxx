#ifndef SERIALIZE_H
#define SERIALIZE_H

#include "types.h"
#include "db.h"

struct Trace;

struct OrderedDB : DB
{
  bool hasValue(Node * node);
  VentureValuePtr getValue(Node * node);
  void registerValue(Node * node, VentureValuePtr value);

  OrderedDB(Trace * trace, vector<VentureValuePtr> values);
  OrderedDB(Trace * trace);
  vector<VentureValuePtr> listValues() { return stack; }

private:
  Trace * trace;
  vector<VentureValuePtr> stack;
};

#endif
