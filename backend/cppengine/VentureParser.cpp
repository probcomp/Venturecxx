#include "HeaderPre.h"
#include "Header.h"
#include "VentureParser.h"
#include "VentureValues.h"
#include "boost/shared_ptr.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/algorithm/string.hpp"

// Parser implementation is inspired by: http://howtowriteaprogram.blogspot.com/2010/11/lisp-interpreter-in-90-lines-of-c.html

bool IsInteger(const string& input) {
  try {
    boost::lexical_cast<int>(input);
  } catch(boost::bad_lexical_cast&) {
    return false;
  }
  return true;
}

bool IsReal(const string& input) {
  try {
    boost::lexical_cast<real>(input);
  } catch(boost::bad_lexical_cast&) {
    return false;
  }
  return true;
}

string ToLower(string processing_string) {
  boost::algorithm::to_lower(processing_string);
  return processing_string;
}

shared_ptr<VentureValue> ProcessAtom(const string& token)
{
  if (token == "b[0]" || token == "b[false]") {
    return shared_ptr<VentureValue>(new VentureBoolean(false));
  } else if (token == "b[1]" || token == "b[true]") {
    return shared_ptr<VentureValue>(new VentureBoolean(true));
  } else if (token == "True") { // Deprecated?
    return shared_ptr<VentureValue>(new VentureBoolean(true));
  } else if (token == "False") { // Deprecated?
    return shared_ptr<VentureValue>(new VentureBoolean(false));
  } else if (token == "true") { // Deprecated?
    return shared_ptr<VentureValue>(new VentureBoolean(true));
  } else if (token == "false") { // Deprecated?
    return shared_ptr<VentureValue>(new VentureBoolean(false));
  } else if (token.substr(0, 2) == "c[") {
    string value = token.substr(2, token.length() - 2 - 1);
    return shared_ptr<VentureValue>(new VentureCount(boost::lexical_cast<int>(value)));
  } else if (token.substr(0, 2) == "r[") {
    string value = token.substr(2, token.length() - 2 - 1);
    return shared_ptr<VentureValue>(new VentureReal(boost::lexical_cast<real>(value)));
  } else if (token.substr(0, 2) == "p[") {
    string value = token.substr(2, token.length() - 2 - 1);
    return shared_ptr<VentureValue>(new VentureProbability(boost::lexical_cast<real>(value)));
  } else if (token.substr(0, 2) == "a[") {
    string value = token.substr(2, token.length() - 2 - 1);
    return shared_ptr<VentureValue>(new VentureAtom(boost::lexical_cast<int>(value)));
  } else if (token.substr(0, 3) == "sc[") {
    string value = token.substr(3, token.length() - 3 - 1);
    return shared_ptr<VentureValue>(new VentureSmoothedCount(boost::lexical_cast<real>(value)));
  } else if (token.substr(0, 3) == "sp[") {
    string value = token.substr(3, token.length() - 3 - 1);
    vector<string> elements_as_strings;
    boost::split(elements_as_strings, value, boost::is_any_of(",")); // Here and in other places we should catch Boost exceptions!
    vector<real> elements;
    for (size_t index = 0; index < elements_as_strings.size(); index++) {
      elements.push_back(boost::lexical_cast<real>(elements_as_strings[index]));
    }
    return shared_ptr<VentureValue>(new VentureSimplexPoint(elements));
  } else if (token.substr(0, 4) == "scv[") {
    string value = token.substr(4, token.length() - 4 - 1);
    vector<string> elements_as_strings;
    boost::split(elements_as_strings, value, boost::is_any_of(","));
    vector<real> elements;
    for (size_t index = 0; index < elements_as_strings.size(); index++) {
      elements.push_back(boost::lexical_cast<real>(elements_as_strings[index]));
    }
    return shared_ptr<VentureValue>(new VentureSmoothedCountVector(elements));
  } else if (token.substr(0, 4) == "str[") {
    string value = token.substr(4, token.length() - 4 - 1);
    return shared_ptr<VentureValue>(new VentureString(boost::lexical_cast<string>(value)));
  } else {
    return shared_ptr<VentureValue>(new VentureSymbol(token));
  }
}

string Stringify(shared_ptr<VentureValue> const value) {
  if (value->GetType() == NIL) { // Why NIL is special?
    return "#nil";
  } else {
    return value->GetString();
  }
}

bool CompareValue(shared_ptr<VentureValue> first, shared_ptr<VentureValue> second) {
  if (first->GetType() == second->GetType()) { // What about LIST and NIL?
    return first->CompareByValue(second);
  } else {
    return false;
  }
}
