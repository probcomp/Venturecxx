#ifndef UTILS_H
#define UTILS_H

#include "all.h"

#include <vector>

struct VentureList;
struct VentureValue;

VentureValue * listRef(VentureList * pair,size_t n);

size_t listLength(VentureList * list);

void listShallowDestroy(VentureList * list);

double sumVector(const vector<double> & xs);
void normalizeVector(vector<double> & xs);

void destroyExpression(VentureValue * exp);

#endif
