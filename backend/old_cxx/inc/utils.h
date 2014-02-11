#ifndef UTILS_H
#define UTILS_H

#include "all.h"

#include <iostream>
#include <vector>
#include <cstdint>
#include <gsl/gsl_rng.h>

struct VentureList;
struct VentureValue;


VentureValue * listRef(VentureList * pair,size_t n);

size_t listLength(VentureList * list);

void listShallowDestroy(VentureList * list);

double sumVector(const vector<double> & xs);
void normalizeVector(vector<double> & xs);

void destroyExpression(VentureValue * exp);

uint32_t sampleCategorical(vector<double> xs, gsl_rng * rng);

template <typename T>
T* value_cast(VentureValue* x) {
  T* answer = dynamic_cast<T*>(x);
  if (answer == nullptr) {
    cout << "Venture type error" << endl;
    throw "Venture type error";
  } else {
    return answer;
  }
}

#endif
