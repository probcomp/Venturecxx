#include "env.h"
#include "node.h"
#include <iostream>
#include <cassert>

Node * Environment::findSymbol(const string & sym)
{
  if (frame.count(sym)) 
  { 
    return frame[sym]; 
  }
  else if (outerEnvNode == nullptr) 
  { 
    cout << "Cannot find symbol: " << sym << endl;
    assert(outerEnvNode);
    return nullptr;
  }
  else return outerEnvNode->getEnvironment()->findSymbol(sym);
}
