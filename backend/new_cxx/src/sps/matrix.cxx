// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "sps/matrix.h"
#include "Eigen/Dense"

#include "utils.h"

using Eigen::MatrixXd;
using Eigen::VectorXd;

VentureValuePtr MatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("matrix", args, 1);

  uint32_t rows, cols;

  vector<VentureValuePtr> allRows = args->operandValues[0]->getArray();
  rows = allRows.size();
  //  assert(rows > 0);

  if (rows == 0) { return VentureValuePtr(new VentureMatrix(MatrixXd(0,0))); }

  // Vector becomes a vector, I guess
  if (NULL != dynamic_pointer_cast<VentureNumber>(allRows[0]))
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
  checkArgsLength("id_matrix", args, 1);

  int dim = args->operandValues[0]->getInt();
  
  return VentureValuePtr(new VentureMatrix(MatrixXd::Identity(dim, dim)));
}

VentureValuePtr IsMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("is_matrix", args, 1);

  return VentureValuePtr(new VentureBool(NULL != dynamic_pointer_cast<VentureMatrix>(args->operandValues[0])));
}

VentureValuePtr TransposeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("transpose", args, 1);

  MatrixXd m = args->operandValues[0]->getMatrix();
  return VentureValuePtr(new VentureMatrix(m.transpose()));
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
  checkArgsLength("is_vector", args, 1);

  return VentureValuePtr(new VentureBool(NULL != dynamic_pointer_cast<VentureVector>(args->operandValues[0])));
}

VentureValuePtr ToVectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("to_vector", args, 1);

  vector<VentureValuePtr> row = args->operandValues[0]->getArray();

  if (row.size() == 0) { return VentureValuePtr(new VentureVector(VectorXd())); }
  else
  {
    VectorXd v(row.size());

    for (size_t i = 0; i < row.size(); ++i) { v(i) = row[i]->getDouble(); }
    return VentureValuePtr(new VentureVector(v));
  }
}



// Arithmetic

VentureValuePtr VectorAddOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("vector_add", args, 2);

  VectorXd v1 = args->operandValues[0]->getVector();
  VectorXd v2 = args->operandValues[1]->getVector();
  return VentureValuePtr(new VentureVector(v1+v2));
}

VentureValuePtr MatrixAddOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("matrix_add", args, 2);

  MatrixXd m1 = args->operandValues[0]->getMatrix();
  MatrixXd m2 = args->operandValues[1]->getMatrix();
  return VentureValuePtr(new VentureMatrix(m1+m2));
}

VentureValuePtr ScaleVectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("scale_vector", args, 2);

  double s = args->operandValues[0]->getDouble();
  VectorXd v = args->operandValues[1]->getVector();
  return VentureValuePtr(new VentureVector(s*v));
}

VentureValuePtr ScaleMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("scale_matrix", args, 2);

  double s = args->operandValues[0]->getDouble();
  MatrixXd m = args->operandValues[1]->getMatrix();
  return VentureValuePtr(new VentureMatrix(s*m));
}

VentureValuePtr VectorDotOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("vector_dot", args, 2);

  VectorXd v1 = args->operandValues[0]->getVector();
  VectorXd v2 = args->operandValues[1]->getVector();
  return VentureValuePtr(new VentureNumber(v1.dot(v2)));
}

VentureValuePtr MatrixMulOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("matrix_mul", args, 2);

  MatrixXd m1 = args->operandValues[0]->getMatrix();
  MatrixXd m2 = args->operandValues[1]->getMatrix();
  MatrixXd ans = m1*m2;
  return VentureValuePtr(new VentureMatrix(ans));
}

VentureValuePtr MatrixTimesVectorOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("matrix_times_vector", args, 2);

  MatrixXd m = args->operandValues[0]->getMatrix();
  VectorXd v = args->operandValues[1]->getVector();
  VectorXd ans = m*v;
  return VentureValuePtr(new VentureVector(ans));
}

VentureValuePtr VectorTimesMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("vector_times_matrix", args, 2);

  VectorXd v = args->operandValues[0]->getVector();
  MatrixXd m = args->operandValues[1]->getMatrix();
  VectorXd ans = v.transpose()*m;
  return VentureValuePtr(new VentureVector(ans));
}
