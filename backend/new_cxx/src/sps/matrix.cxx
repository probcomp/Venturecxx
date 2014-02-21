#include "sps/matrix.h"

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
    assert(cols == row_i.size());
    
    for (size_t j = 0; j < cols; ++j)
    {
      M(i,j) = row_i[j]->getDouble();
    }
  }
  return VentureValuePtr(new VentureMatrix(M));
}

VentureValuePtr IsMatrixOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  cout << "isMatrixOutputPSP::simulate" << endl;
  return VentureValuePtr(new VentureBool(dynamic_pointer_cast<VentureMatrix>(args->operandValues[0])));
}
