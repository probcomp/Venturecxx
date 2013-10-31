
// Scheme Interpreter in 90 lines of C++ (not counting lines after the first 90).
// Inspired by Peter Norvig's Lis.py.

// Made by Anthony C. Hay in 2010. See http://howtowriteaprogram.blogspot.co.uk/
// This is free and unencumbered public domain software, see http://unlicense.org/
// This code is known to have faults. E.g. it leaks memory. Use at your own risk.

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <list>
#include <map>

#include <iostream>
using std::cout;
using std::endl;

// return true iff given character is '0'..'9'
bool isdig(char c) { return isdigit(static_cast<unsigned char>(c)) != 0; }


////////////////////// cell

enum cell_type { Symbol, Number, List, Proc, Lambda };

// a variant that can hold any kind of lisp value
struct cell {
  typedef cell (*proc_type)(const std::vector<cell> &);
  typedef std::vector<cell>::const_iterator iter;
  typedef std::map<std::string, cell> map;
  cell_type type; std::string val; std::vector<cell> list; proc_type proc; 
  cell(cell_type type = Symbol) : type(type) {}
  cell(cell_type type, const std::string & val) : type(type), val(val) {}
  cell(proc_type proc) : type(Proc), proc(proc) {}
};

typedef std::vector<cell> cells;
typedef cells::const_iterator cellit;

const cell false_sym(Symbol, "#f");
const cell true_sym(Symbol, "#t"); // anything that isn't false_sym is true
const cell nil(Symbol, "nil");


void eval(cell x)
{
  if (x.type == Symbol) 
    { cout << "Symbol: " << x.val << endl; }
  else if (x.type == Number)
    { cout << "Number: " << x.val << endl; }
  else if (x.list.empty())
    { cout << "<nil>" << endl; }
  else if (x.list[0].type == Symbol) {
    if (x.list[0].val == "quote")
      { cout << x.list[0].val << x.list[1].val << endl; }
    else if (x.list[0].val == "lambda")
      { cout << x.list[0].val << x.list[1].val << x.list[2].val << endl; }
    else
      { cout << "<proc>" << x.list[0].val << x.list[1].val << endl; }
  }
}

////////////////////// parse, read and user interaction

// convert given string to list of tokens
std::list<std::string> tokenize(const std::string & str)
{
  std::list<std::string> tokens;
  const char * s = str.c_str();
  while (*s) {
    while (*s == ' ')
      ++s;
    if (*s == '(' || *s == ')')
      tokens.push_back(*s++ == '(' ? "(" : ")");
    else {
      const char * t = s;
      while (*t && *t != ' ' && *t != '(' && *t != ')')
	++t;
      tokens.push_back(std::string(s, t));
      s = t;
    }
  }
  return tokens;
}

// numbers become Numbers; every other token is a Symbol
cell atom(const std::string & token)
{
  if (isdig(token[0]) || (token[0] == '-' && isdig(token[1])))
    return cell(Number, token);
  return cell(Symbol, token);
}

// return the Lisp expression in the given tokens
cell read_from(std::list<std::string> & tokens)
{
  const std::string token(tokens.front());
  tokens.pop_front();
  if (token == "(") {
    cell c(List);
    while (tokens.front() != ")")
      c.list.push_back(read_from(tokens));
    tokens.pop_front();
    return c;
  }
  else
    return atom(token);
}

// return the Lisp expression represented by the given string
cell read(const std::string & s)
{
  std::list<std::string> tokens(tokenize(s));
  return read_from(tokens);
}

// convert given cell to a Lisp-readable string
std::string to_string(const cell & exp)
{
  if (exp.type == List) {
    std::string s("(");
    for (cell::iter e = exp.list.begin(); e != exp.list.end(); ++e)
      s += to_string(*e) + ' ';
    if (s[s.size() - 1] == ' ')
      s.erase(s.size() - 1);
    return s + ')';
  }
  else if (exp.type == Lambda)
    return "<Lambda>";
  else if (exp.type == Proc)
    return "<Proc>";
  return exp.val;
}

// the default read-eval-print-loop
void repl(const std::string & prompt)
{
  for (;;) {
    std::cout << prompt;
    std::string line; std::getline(std::cin, line);
    eval(read(line));
  }
}

int main ()
{
  repl("90> ");
}
