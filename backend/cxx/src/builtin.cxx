#include "builtin.h"

#include "sps/real.h"
#include "sps/count.h"
#include "sps/bool.h"
#include "sps/continuous.h"
#include "sps/discrete.h"
#include "sps/csp.h"
#include "sps/mem.h"
#include "sps/cond.h"
#include "sps/eval.h"
#include "sps/envs.h"
#include "sps/pycrp.h"

#include "sps/makesymdirmult.h"
#include "sps/makeucsymdirmult.h"
#include "sps/makelazyhmm.h"

#include "sps/vector.h"
#include "sps/list.h"
#include "sps/map.h"

/* GC All new calls in both of these functions will be freed
   by Trace's destructor. */
map<string,VentureValue *> initBuiltInValues()
{
  return 
  { 
    {"true",new VentureBool(true)},
    {"false",new VentureBool(false)}
  };
}

map<string,SP *> initBuiltInSPs()
{
  return
  {
    {"real_plus", new RealPlusSP},
    {"real_minus", new RealMinusSP},
    {"real_times", new RealTimesSP},
    {"real_div", new RealDivideSP},
    {"real_eq", new RealEqualSP},
    {"real_gt", new RealGreaterThanSP},
    {"real_lt", new RealLessThanSP},

    {"uint_plus", new CountPlusSP},
    {"uint_minus", new CountMinusSP},
    {"uint_times", new CountTimesSP},
    {"uint_div", new CountDivideSP},
    {"uint_eq", new CountEqualSP},
    {"uint_gt", new CountGreaterThanSP},
    {"uint_lt", new CountLessThanSP},

    {"pair", new PairSP},
    {"first", new FirstSP},
    {"rest", new RestSP},
    {"list", new ListSP},
    {"pair?", new IsPairSP},
    {"list_ref", new ListRefSP},
    {"map_list", new MapListSP},

    {"make_vector", new MakeVectorSP},
    {"vector_lookup", new VectorLookupSP},

    {"make_map", new MakeMapSP},
    {"map_lookup", new MapLookupSP},
    
    {"and", new BoolAndSP},
    {"or", new BoolOrSP},
    {"not", new BoolNotSP},
    {"xor", new BoolXorSP},

    {"bernoulli", new BernoulliSP},
    {"categorical", new CategoricalSP},

    {"normal", new NormalSP},
    {"gamma", new GammaSP},
    {"uniform_continuous", new UniformContinuousSP},

    {"make_crp", new MakePitmanYorCRPSP},

    {"branch", new BranchSP},

    {"mem", new MSPMakerSP},

    {"get_current_environment", new GetCurrentEnvSP},
    {"get_empty_environment", new GetEmptyEnvSP},
    {"extend_environment", new ExtendEnvSP},
    {"eval", new EvalSP},

    {"make_sym_dir_mult", new MakeSymDirMultSP},
    {"make_uc_sym_dir_mult", new MakeUCSymDirMultSP},

    {"make_lazy_hmm", new MakeLazyHMMSP},
      };
}
   
