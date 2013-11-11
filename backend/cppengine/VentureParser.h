
#ifndef VENTURE___VENTURE_PARSER_H
#define VENTURE___VENTURE_PARSER_H

// Parsed implementation is inspired by: http://howtowriteaprogram.blogspot.com/2010/11/lisp-interpreter-in-90-lines-of-c.html

#include "Header.h"
#include "VentureValues.h"

bool IsInteger(const string&);

bool IsReal(const string&);

string ToLower(string);

shared_ptr<VentureValue> ProcessAtom(const string&);

shared_ptr<VentureValue> ProcessTokens(list<string>&);

shared_ptr<VentureValue> ReadCode(const string&);

string Stringify(shared_ptr<VentureValue> const);

bool CompareValue(shared_ptr<VentureValue>, shared_ptr<VentureValue>);

#endif
