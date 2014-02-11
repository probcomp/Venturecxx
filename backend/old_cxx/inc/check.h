#ifndef CHECK_H
#define CHECK_H

struct Trace;
struct Scaffold;

struct TraceConsistencyChecker
{
  TraceConsistencyChecker(Trace * trace): trace(trace) {}
  Trace * trace;
  
  void checkConsistency();


  void checkTorus(Scaffold * scaffold);
  void checkWhole(Scaffold * scaffold);

};



#endif
