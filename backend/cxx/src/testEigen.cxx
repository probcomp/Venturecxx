#include <iostream>
#include "Eigen/Dense"

#include <string>
#include <typeinfo>

#include <cmath>

using Eigen::MatrixXd;
using Eigen::VectorXd;
using namespace std;

int main()
{
  MatrixXd m(2,2);
  m(0,0) = 3;
  m(1,0) = 2.5;
  m(0,1) = -1;
  m(1,1) = m(1,0) + m(0,1);
  cout << m << endl;

  VectorXd v(5);
  size_t vs = v.size();
  cout << "Vector size: " << vs << endl;
  cout << "Vector size type: " << typeid(v.size()).name() << endl;

  cout << m.size() << endl;
  size_t r = m.rows();
  size_t c = m.cols();
  cout << "m.rows(), m.cols() = " << r << ", " << c << endl;

  double lzero = log(0);
  cout << "log(0): " << lzero << endl;
  double bzero = exp(lzero);
  cout << "exp(log(0)): " << bzero << endl;
  
}
