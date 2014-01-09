#ifndef SIMULATOR_H
#define SIMULATOR_H

#include "sp.h"
#include "spaux.h"
#include <vector>
#include <string>
#include "engine.h"

struct SymDirMultSPAux : SPAux
{
  Engine *ep{nullptr};
  uint32_t next_id{0};
};

struct MakeSimulatorSP : SP
{
  MakeSimulatorSP()
    {
      name = "make_simulator";
    }
  // example: [ASSUME simulator (make_simulator 'sim1)]
  // sim1 is the subfolder in the matlab folder
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;

};

struct SimulatorSP : SP
{
  SimulatorSP(string subfolder)
    {
      isRandomOutput = true;
      name = "simulator";
      path_to_folder = "MATLAB/Simulators/" + subfolder;
    }

  //dispatch is based on the first arg eg 
  // (simulator 'simulate' old_state params)
  //   read data from FILE old_state
  //   store new state in new, uniquely named FILE
  //   return VentureToken(new_filename) which is then passed as the old_state
  //   to the next time step
  // (simulator 'emit' state params)
  //   return new VentureToken(new_filename) which contains the emission
  // (simulator 'distance' real_data obs_data)  
  //   real_data and obs_data are both filenames in the specified folder
  //   (real_data is named by the user whereas obs_data is named by the simulator)
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;

  //TODO add compute_logdensity and absorb for some of the methods

  //init matlab engine
  SPAux * constructSPAux() const override;

  //close matlab engine
  void destroySPAux(SPAux * spaux) const override;

  string pathToFolder; // "MATLAB/Simulators/sim1" in the above example
};



#endif
