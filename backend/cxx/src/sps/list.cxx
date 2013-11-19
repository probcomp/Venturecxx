#include "sps/list.h"
#include "value.h"

#include "utils.h"
#include "env.h"
#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;


VentureValue * PairSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureValue * first = args.operands[0];
  VentureList * rest = dynamic_cast<VentureList *>(args.operands[1]);
  assert(rest);
  return new VenturePair(first,rest);
}

VentureValue * FirstSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VenturePair * pair = dynamic_cast<VenturePair*>(args.operands[0]);
  assert(pair);
  return pair->first;
}

VentureValue * RestSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VenturePair * pair = dynamic_cast<VenturePair*>(args.operands[0]);
  assert(pair);
  return pair->rest;
}

VentureValue * ListSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureList * list = new VentureNil;
  for (VentureValue * operand : reverse(args.operands))
  {
    list = new VenturePair(operand,list);
  }
  return list;
}

void ListSP::flushOutput(VentureValue * value) const 
{
  VentureList * list = dynamic_cast<VentureList*>(value);
  listShallowDestroy(list);
}

VentureValue * IsPairSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  return new VentureBool(dynamic_cast<VenturePair*>(args.operands[0]));
}

VentureValue * ListRefSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureList * list = dynamic_cast<VentureList*>(args.operands[0]);
  VentureNumber * index = dynamic_cast<VentureNumber*>(args.operands[1]);
  assert(list);
  assert(index);
  return listRef(list,index->getInt());
}


VentureValue * MapListSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  VentureValue * fVal = args.operands[0];
  assert(dynamic_cast<VentureSP*>(fVal));

  vector<ESR> esrs;
  VentureList * list = dynamic_cast<VentureList*>(args.operands[1]);
  assert(list);

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("mappedSP"),args.operandNodes[0]);

  size_t i = 0;
  while (!dynamic_cast<VentureNil*>(list))
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);

    VentureValue * val = new VenturePair(new VentureSymbol("quote"),
					 new VenturePair(pair->first,
							 new VentureNil));
    assert(val);
 
    /* TODO this may be problematic */
    size_t id = reinterpret_cast<size_t>(args.outputNode) + i;

    VenturePair * exp = new VenturePair(new VentureSymbol("mappedSP"),
					new VenturePair(val,
							new VentureNil));


    esrs.push_back(ESR(id,exp,env));
    i++;
    list = pair->rest;
  }
  return new VentureRequest(esrs);
}


void MapListSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  vector<ESR> esrs = requests->esrs;
  if (!esrs.empty())
  {
    esrs[0].env->destroySymbols();
    delete esrs[0].env;

    for (ESR esr : esrs)
    {
      VenturePair * exp = dynamic_cast<VenturePair*>(esr.exp);
      assert(exp);
      delete exp->first;
      VenturePair * quote = dynamic_cast<VenturePair*>(exp->rest);
      assert(quote);
      delete quote->first;
      listShallowDestroy(exp);
    }
  }
  
  delete value;
}

VentureValue * MapListSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureList * list = new VentureNil;
  for (VentureValue * esr : reverse(args.esrs))
  {
     list = new VenturePair(esr,list);
  }
  return list;
}

void MapListSP::flushOutput(VentureValue * value) const
{
  VentureList * list = dynamic_cast<VentureList*>(value);
  listShallowDestroy(list);
}







