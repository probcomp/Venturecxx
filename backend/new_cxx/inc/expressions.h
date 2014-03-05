#ifndef EXPRESSIONS_H
#define EXPRESSIONS_H

#include "types.h"

bool isVariable(VentureValuePtr exp);
bool isSelfEvaluating(VentureValuePtr exp);
bool isQuotation(VentureValuePtr exp);

VentureValuePtr textOfQuotation(VentureValuePtr exp);


#endif
