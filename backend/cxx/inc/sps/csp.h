#ifndef CSP_SP_H
#define CSP_SP_H

#include "exp.h"
#include "sp.h"
#include <vector>
#include <string>

struct CSP : SP
{
  /* TODO GC major GC issue with values. Right now the values in the expression
     will be shared by all applications of the csp! */
  CSP(const vector<string> ids, Expression & body, Node * envNode,bool ownsExp): 
    ids(ids), body(body), envNode(envNode), ownsExp(ownsExp)
    { 
      isESRReference = true;
      makesESRs = true;
    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;

  void destroyValuesInExp(Expression & exp);
  ~CSP();

  vector<string> ids; 
  Expression body;
  Node * envNode;
  bool ownsExp;
};




#endif
