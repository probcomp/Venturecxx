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
