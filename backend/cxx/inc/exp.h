#ifndef EXPRESSION_H
#define EXPRESSION_H

#include <string>
#include <vector>

#include <stdlib.h>
#include <cassert>

using namespace std;

struct VentureValue;

enum class ExpType { VALUE,VARIABLE,LAMBDA,APPLICATION };

/* TODO OPT make this a union */
struct Expression
{
  Expression(vector<Expression> exps): 
    expType(ExpType::APPLICATION), exps(exps)
    {
      /* Awkward */
      if (!exps.empty() && exps[0].expType == ExpType::VARIABLE && exps[0].sym == "lambda")
      { expType = ExpType::LAMBDA; }
    }

  Expression(string sym): expType(ExpType::VARIABLE), sym(sym) {}
  Expression(VentureValue * value): expType(ExpType::VALUE), value(value) {}
  
  ExpType expType;

  vector<Expression> exps;
  string sym;
  VentureValue * value{nullptr};
  
  vector<string> getIDs();

};






#endif
