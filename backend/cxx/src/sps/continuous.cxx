#include "node.h"
#include "sp.h"
#include "sps/continuous.h"
#include "value.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cmath>
#include <vector>

#include <iostream>

/* Normal */
VentureValue * NormalSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  double mu = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  double sigma = dynamic_cast<VentureDouble *>(operands[1]->getValue())->x;
  double x = gsl_ran_gaussian(rng, sigma) + mu;
  return new VentureDouble(x);
}

double NormalSP::logDensityOutput(VentureValue * value, Node * node) 
{
  std::vector<Node *> operands = node->operandNodes;
  double mu = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  double sigma = dynamic_cast<VentureDouble *>(operands[1]->getValue())->x;
  double x = dynamic_cast<VentureDouble *>(value)->x;
  return log(gsl_ran_gaussian_pdf(x - mu, sigma));
}

/* Gamma */
VentureValue * GammaSP::simulateOutput(Node * node, gsl_rng * rng) 
{
  std::vector<Node *> operands = node->operandNodes;
  double a = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  double b = dynamic_cast<VentureDouble *>(operands[1]->getValue())->x;
  double x = gsl_ran_gamma(rng, a, b);
  return new VentureDouble(x);
}

double GammaSP::logDensityOutput(VentureValue * value, Node * node) 
{
  std::vector<Node *> operands = node->operandNodes;
  double a = dynamic_cast<VentureDouble *>(operands[0]->getValue())->x;
  double b = dynamic_cast<VentureDouble *>(operands[1]->getValue())->x;
  double x = dynamic_cast<VentureDouble *>(value)->x;
  return gsl_ran_gamma_pdf(x, a, b);
}

