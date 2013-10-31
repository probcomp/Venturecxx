#ifndef EXPRESSION_H
#define EXPRESSION_H

#include <string>
#include <vector>

#include "value.h"

#include <stdlib.h>
#include <cassert>

enum class ExpType { VALUE,VARIABLE,LAMBDA,APPLICATION };

/* TODO OPT make this a union */
struct Expression
{
  Expression(std::vector<Expression> exps): 
    expType(ExpType::APPLICATION), exps(exps)
    {
      assert(!exps.empty());
      /* Awkward */
      if (exps[0].expType == ExpType::VARIABLE && exps[0].sym == "lambda")
      { expType = ExpType::LAMBDA; }
    }

  Expression(std::string sym): expType(ExpType::VARIABLE), sym(sym) {}

  Expression(VentureValue * value): expType(ExpType::VALUE), value(value) {}
  
  ExpType expType;

  std::vector<Expression> exps;
  std::string sym;
  VentureValue * value{nullptr};

  std::vector<std::string> getIDs();
  /* TODO GC */

};






#endif
