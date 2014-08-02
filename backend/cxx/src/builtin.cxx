/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "builtin.h"

#include "sps/number.h"
#include "sps/trig.h"
#include "sps/bool.h"
#include "sps/continuous.h"
#include "sps/discrete.h"
#include "sps/csp.h"
#include "sps/mem.h"
#include "sps/cond.h"
#include "sps/sym.h"
#include "sps/eval.h"
#include "sps/envs.h"
#include "sps/pycrp.h"

#include "sps/makesymdirmult.h"
#include "sps/makeucsymdirmult.h"
#include "sps/makedirmult.h"
#include "sps/makebetabernoulli.h"
#include "sps/makelazyhmm.h"

#include "sps/vector.h"
#include "sps/matrix.h"
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
    // numbers
    {"plus", new PlusSP},
    {"minus", new MinusSP},
    {"times", new TimesSP},
    {"div", new DivideSP},
    {"power", new PowerSP},
    {"pow", new PowerSP},
    {"eq", new EqualSP},
    {"gt", new GreaterThanSP},
    {"lt", new LessThanSP},
    {"gte", new GreaterThanOrEqualToSP},
    {"lte", new LessThanOrEqualToSP},
    {"real", new RealSP},
    
    // integers
    {"int_plus", new IntPlusSP},
    {"int_minus", new IntMinusSP},
    {"int_times", new IntTimesSP},
    {"int_div", new IntDivideSP},
    {"int_eq", new IntEqualSP},

    // atoms
    {"atom_eq", new AtomEqualSP},

    // symbols
    {"is_symbol", new IsSymbolSP},


    // trig
    {"sin", new SinSP},
    {"cos", new CosSP},

    // lists
    {"pair", new PairSP},
    {"first", new FirstSP},
    {"rest", new RestSP},
    {"list", new ListSP},
    {"is_pair", new IsPairSP},
    {"list_ref", new ListRefSP},
    {"map_list", new MapListSP},

    // vectors
    {"simplex", new MakeVectorSP},
    {"array", new MakeVectorSP},
    {"array_lookup", new VectorLookupSP},

    // matrices
    {"matrix", new MakeMatrixSP}, 
    {"matrix_lookup", new MatrixLookupSP},

    // maps
    {"dict", new MakeMapSP},
    {"contains", new MapContainsSP},
    {"dict_lookup", new MapLookupSP},

    {"lookup", new GenericLookupSP},
    
    // booleans
    {"and", new BoolAndSP},
    {"or", new BoolOrSP},
    {"not", new BoolNotSP},
    {"xor", new BoolXorSP},

    // discrete distributions
    {"flip", new BernoulliSP},
    {"bernoulli", new BernoulliSP},
    {"categorical", new CategoricalSP},
    {"uniform_discrete", new UniformDiscreteSP},
    {"poisson", new PoissonSP},

    // continuous distributions
    {"normal", new NormalSP},
    {"gamma", new GammaSP},
    {"inv_gamma", new InvGammaSP},
    {"uniform_continuous", new UniformContinuousSP},
    {"beta", new BetaSP},
    {"student_t", new StudentTSP},
    {"chisq", new ChiSquareSP},
    {"inv_chisq", new InverseChiSquareSP},

    // control flow
    {"branch", new BranchSP},
    {"biplex", new BiplexSP},

    // environments
    {"get_current_environment", new GetCurrentEnvSP},
    {"get_empty_environment", new GetEmptyEnvSP},
    {"extend_environment", new ExtendEnvSP},
    {"eval", new EvalSP},

    // exchangeable random procedures
    {"make_sym_dir_mult", new MakeSymDirMultSP},
    {"make_uc_sym_dir_mult", new MakeUCSymDirMultSP},
    {"make_dir_mult", new MakeDirMultSP},
    {"make_beta_bernoulli", new MakeBetaBernoulliSP},

    {"make_crp", new MakePitmanYorCRPSP},

    // with LSRs
    {"make_lazy_hmm", new MakeLazyHMMSP},

    // Lambda replacement
    {"make_csp", new MakeCSP},

    // with shared ESRs
    {"mem", new MakeMSP},
  };
}

