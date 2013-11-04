#include "aekernel.h"

void AECycleKernel::simulate()
{
  for (AEKernel * k : aekernels)
  {

  }

}
struct AECycleKernel : AEKernel
{
  AECycleKernel(vector<AEKernel *> aekernels): aekernels(aekernels) {}
  void simulate();
};
