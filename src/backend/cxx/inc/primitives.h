#ifndef PRIMITIVES_H
#define PRIMITIVES_H

#include "address.h"
#include "value.h"
#include "value_types.h"

#include "sps/float.h"
#include "sps/bool.h"
#include "sps/continuous.h"
#include "sps/csp.h"

const std::map<std::string,VentureValue *> builtInValues = 
  { 
    {"true",new VentureBool(true)},
    {"false",new VentureBool(false)}
  };

const std::map<std::string,VentureSPValue *> builtInSPs =
  {
    /* Float */
    {"float_plus", new VentureSPValue(new FloatPlusSP("float_plus"))},
    {"float_times",new VentureSPValue(new FloatTimesSP("float_times"))},
    {"float_divide",new VentureSPValue(new FloatDivideSP("float_divide"))},
    {"float_equal",new VentureSPValue(new FloatEqualSP("float_equal"))},
    {"float_gt",new VentureSPValue(new FloatGreaterThanSP("float_gt"))},
    {"float_lt",new VentureSPValue(new FloatLessThanSP("float_lt"))},

    /* Bool */
    {"and",new VentureSPValue(new BoolAndSP("and"))},
    {"or",new VentureSPValue(new BoolOrSP("or"))},
    {"not",new VentureSPValue(new BoolNotSP("not"))},
    {"xor",new VentureSPValue(new BoolXorSP("xor"))},

    /* Continuous */
    {"normal",new VentureSPValue(new NormalSP("normal"))},
    {"gamma",new VentureSPValue(new GammaSP("gamma"))},


  };
   
#endif
