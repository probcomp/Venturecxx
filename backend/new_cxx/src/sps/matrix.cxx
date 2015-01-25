#include "sps/matrix.h"
#include "Eigen/Dense"

using Eigen::MatrixXd;
using Eigen::VectorXd;

VentureValuePtr MatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  uint32_t rows, cols;

  vector<VentureValuePtr> allRows = args->operandValues[0]->getArray();
  rows = allRows.size();
  //  assert(rows > 0);

  if (rows == 0) { return VentureValuePtr(new VentureMatrix(MatrixXd(0,0))); }

  // Vector becomes a vector, I guess
  if (dynamic_pointer_cast<VentureNumber>(allRows[0]))
  { 
    VectorXd v(rows);

    for (size_t i = 0; i < rows; ++i) { v(i) = allRows[i]->getDouble(); }
    return VentureValuePtr(new VentureMatrix(v));
  }
 
  vector<VentureValuePtr> row0 = allRows[0]->getArray();
  cols = row0.size();
  //  assert(cols > 0);

  MatrixXd M(rows,cols);

  for (size_t i = 0; i < rows; ++i)
  {
    vector<VentureValuePtr> row_i = allRows[i]->getArray();
    if (cols != row_i.size()) { throw "Matrix must have equal number of elements per row."; }
    
    for (size_t j = 0; j < cols; ++j)
    {
      M(i,j) = row_i[j]->getDouble();
    }
  }
  return VentureValuePtr(new VentureMatrix(M));
}

VentureValuePtr IdentityMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  int dim = args->operandValues[0]->getInt();
  
  return VentureValuePtr(new VentureMatrix(MatrixXd::Identity(dim, dim)));
}

VentureValuePtr IsMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureMatrix>(args->operandValues[0]) != NULL));
}



////////////// Vector

VentureValuePtr VectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> row = args->operandValues;

  if (row.size() == 0) { return VentureValuePtr(new VentureVector(VectorXd())); }
  else
  {
    VectorXd v(row.size());

    for (size_t i = 0; i < row.size(); ++i) { v(i) = row[i]->getDouble(); }
    return VentureValuePtr(new VentureVector(v));
  }
}

VentureValuePtr IsVectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureVector>(args->operandValues[0])));
}

VentureValuePtr ToVectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  vector<VentureValuePtr> row = args->operandValues[0]->getArray();

  if (row.size() == 0) { return VentureValuePtr(new VentureVector(VectorXd())); }
  else
  {
    VectorXd v(row.size());

    for (size_t i = 0; i < row.size(); ++i) { v(i) = row[i]->getDouble(); }
    return VentureValuePtr(new VentureVector(v));
  }
}
