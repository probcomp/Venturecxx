#ifndef GKERNEL_H
#define GKERNEL_H

struct GKernel
{
  double propose(ConcreteTrace * trace,
		 shared_ptr<Scaffold> scaffold);

  void accept();
  void reject();
};


#endif
