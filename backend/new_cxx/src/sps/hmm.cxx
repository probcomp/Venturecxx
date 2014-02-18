// struct HMMSPAux : SPAux
// {
//   /* Latents */
//   vector<VectorXd> xs; 
  
//   /* Observations: may be many observations at a single index */
//   /* We expect very few, otherwise we would use a set */
//   map<size_t,vector<uint32_t> > os;
// };

/* MakeUncollapsedHMMSP */

#include "sps/hmm.h"
#include "args.h"
#include "sprecord.h"

VectorXd vvToEigenVector(VentureValue * value);
MatrixXd vvToEigenMatrix(VentureValue * value);
uint32_t indexOfOne(const VectorXd & v);
VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng);
uint32_t sampleVector(const VectorXd & v,gsl_rng * rng);
VectorXd normalizedVectorXd(VectorXd & v);


VentureValuePtr MakeUncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{ 
  MatrixXd p0 = args->operandValues[0]->getMatrix();
  MatrixXd T = args->operandValues[1]->getMatrix();
  MatrixXd O = args->operandValues[0]->getMatrix();
  return VentureValuePtr( 
    new VentureSPRecord(
      new UncollapsedHMMSP(
	new UncollapsedHMMRequestPSP(),
	new UncollapsedHMMOutputPSP(O),
	p0,
	T,
	O),
      new HMMSPAux()
      ));
}

/* UncollapsedHMMSP */
UncollapsedHMMSP::UncollapsedHMMSP(PSP * requestPSP, PSP * outputPSP,MatrixXd p0,MatrixXd T,MatrixXd O):
  SP(requestPSP,outputPSP), p0(p0), T(T), O(O) {}

shared_ptr<LatentDB> UncollapsedHMMSP::constructLatentDB() const { return shared_ptr<LatentDB>(new HMMLatentDB()); }

double UncollapsedHMMSP::simulateLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,bool shouldRestore,shared_ptr<LatentDB> latentDB,gsl_rng * rng) const 
{ 
  /* if should restore, restore, otherwise do not assert latentDB */
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(spaux);
  assert(aux);

  shared_ptr<HMMLSR> request = dynamic_pointer_cast<HMMLSR>(lsr);
  assert(request);

  shared_ptr<HMMLatentDB> latents;
  if (latentDB)
  { 
    latents = dynamic_pointer_cast<HMMLatentDB>(latentDB);
    assert(latents);
  }
  
  /* No matter what the request is, we must sample the first latent if
     we have not already done so. */
  if (aux->xs.empty()) 
  { 
    if (shouldRestore) { aux->xs.push_back(latents->xs[0]); }
    else { aux->xs.push_back(sampleVectorXd(p0,rng)); }
  }

  if (aux->xs.size() <= request->index)
  {
    for (size_t i = aux->xs.size(); i <= request->index; ++i)
    {
      MatrixXd sample;
      if (shouldRestore) { sample = latents->xs[i]; }
      else { sample = sampleVectorXd(T * aux->xs.back(),rng); }
      aux->xs.push_back(sample);
    }
  }
  assert(aux->xs.size() > request->index);
  return 0;
}

double UncollapsedHMMSP::detachLatents(shared_ptr<SPAux> spaux,shared_ptr<LSR> lsr,shared_ptr<LatentDB> latentDB) const 
{ 
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(spaux);
  assert(aux);

  shared_ptr<HMMLSR> request = dynamic_pointer_cast<HMMLSR>(lsr);
  assert(request);

  shared_ptr<HMMLatentDB> latents = dynamic_pointer_cast<HMMLatentDB>(latentDB);
  assert(latents);

  if (aux->xs.size() == request->index + 1 && 
      !aux->os.count(request->index))
  {
    if (aux->os.empty()) 
    { 
      for (size_t i = 0; i < aux->xs.size(); ++i)
      { latents->xs[i] = aux->xs[i]; }
      aux->xs.clear();
    }
    else
    {
      uint32_t maxObservation = (*(max_element(aux->os.begin(),aux->os.end()))).first;
      for (size_t i = aux->xs.size()-1; i > maxObservation; --i)
      {
	latents->xs[i] = aux->xs.back();
	aux->xs.pop_back();
      }
      assert(aux->xs.size() == maxObservation + 1);
    }
  }
  return 0;
}

void UncollapsedHMMSP::AEInfer(shared_ptr<Args> args, gsl_rng * rng) const { assert(false); }


/* UncollapsedHMMOutputPSP */

UncollapsedHMMOutputPSP::UncollapsedHMMOutputPSP(MatrixXd O): O(O) {}


VentureValuePtr UncollapsedHMMOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const 
{
  shared_ptr<HMMSPAux> aux = dynamic_pointer_cast<HMMSPAux>(args->spAux);
  assert(aux);
  int index = argse->operandValues[0]->getInt();
  assert(aux->xs.size() > index);
  return VentureValuePtr(new VentureAtom(sampleVector(O * aux->xs[index],rng)));
}

double UncollapsedHMMOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }
void UncollapsedHMMOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }
void UncollapsedHMMOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const { assert(false); }


/* UncollapsedHMMRequestPSP */

VentureValuePtr UncollapsedHMMRequestPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const { assert(false); }





/* Matrix utils */
/* Helpers */

VectorXd vvToEigenVector(VentureValue * value)
{
  VentureVector * vvec = dynamic_cast<VentureVector*>(value);
  assert(vvec);

  size_t len = vvec->xs.size();
  VectorXd v(len);

  for (size_t i = 0; i < len; ++i)
  {
    VentureNumber * vdouble = dynamic_cast<VentureNumber*>(vvec->xs[i]);
    assert(vdouble);
    v(i) = vdouble->x;
  }
  return v;
}

MatrixXd vvToEigenMatrix(VentureValue * value)
{
  uint32_t rows, cols;

  VentureVector * allRows = dynamic_cast<VentureVector*>(value);
  assert(allRows);
  rows = allRows->xs.size();
  assert(rows > 0);

  VentureVector * vrow0 = dynamic_cast<VentureVector*>(allRows->xs[0]);
  assert(vrow0);
  cols = vrow0->xs.size();
  assert(cols > 0);

  MatrixXd M(rows,cols);

  for (size_t i = 0; i < rows; ++i)
  {
    VentureVector * vrow = dynamic_cast<VentureVector*>(allRows->xs[i]);
    assert(vrow);
    assert(cols == vrow->xs.size());
    
    for (size_t j = 0; j < cols; ++j)
    {
      VentureNumber * vdouble = dynamic_cast<VentureNumber*>(vrow->xs[j]);
      assert(vdouble);
      M(i,j) = vdouble->x;
    }
  }
  return M;
}

uint32_t indexOfOne(const VectorXd & v)
{
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    if (v[i] == 1) { return i; }
    else { assert(v[i] == 0); }
  }
  assert(false);
  return -1;
}

VectorXd sampleVectorXd(const VectorXd & v,gsl_rng * rng)
{
  VectorXd sample(v.size());
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i) { sample[i] = 0; }

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u <= sum) 
    { 
      sample[i] = 1;
      return sample;
    }
  }
  assert(false);
  return sample;
}

uint32_t sampleVector(const VectorXd & v,gsl_rng * rng)
{
  double u = gsl_ran_flat(rng,0.0,1.0);

  double sum = 0.0;
  size_t len = v.size();
  for (size_t i = 0; i < len; ++i)
  {
    sum += v[i];
    if (u <= sum) { return i; }
  }
  cout << "sum should be 1: " << sum << endl;
  assert(false);
  return -1;
}

VectorXd normalizedVectorXd(VectorXd & v)
{
  
  size_t len = v.size();
  double sum = 0;
  for (size_t i = 0; i < len; ++i) { sum += v[i]; }

  VectorXd newVector(len);
  for (size_t i = 0; i < len; ++i) { newVector[i] = v[i] / sum; }
  return newVector;
}
