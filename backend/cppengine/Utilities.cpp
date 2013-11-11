#include "HeaderPre.h"
#include "Utilities.h"
#include <gsl/gsl_sf.h>

// http://stackoverflow.com/questions/4523178/how-to-print-out-all-elements-in-a-stdstack-or-stdqueue-conveniently
template < class Type, class Container >
const Container& GetQueueContainer
    (const std::queue<Type, Container>& queue)
{
    struct HackedQueue : private std::queue<Type, Container>
    {
        static const Container& GetQueueContainer
            (const std::queue<Type, Container>& queue)
        {
            return queue.*&HackedQueue::c;
        }
    };

    return HackedQueue::GetQueueContainer(queue);
}
template < class Type, class Container >
const Container& GetStackContainer // FIXME: Should be called GetStackContainer!
    (const std::stack<Type, Container>& stack)
{
    struct HackedStack : private std::stack<Type, Container>
    {
        static const Container& container
            (const std::stack<Type, Container>& stack)
        {
            return stack.*&HackedStack::c;
        }
    };

    return HackedStack::container(stack);
}

void BlankFunction___ForGetQueueContainer() { // For some reason without this function
                                              // "GetQueueContainer" is not generated.
  queue< shared_ptr<Node> > touched_nodes;
  GetQueueContainer(touched_nodes);
}

// FIXME: Should be called ...Stack...!
void BlankFunction___ForGetStackContainer() { // For some reason without this function
                                              // "GetQueueContainer" is not generated.
  stack< shared_ptr<Node> > touched_nodes;
  GetStackContainer(touched_nodes);
}

int UniformDiscrete(int a, int b) {
  return static_cast<int>(gsl_ran_flat(random_generator, a, b + 1));
}

real NormalDistributionLogLikelihood(real sampled_value_real, real average, real sigma) {
  double loglikelihood = 0.0;
  loglikelihood -= log(sigma);
  loglikelihood -= 0.5 * log(2.0 * 3.14159265358979323846264338327950);
  loglikelihood -= pow(sampled_value_real - average, 2.0) / (2.0 * pow(sigma, 2.0));
  return loglikelihood;
}

real BetaDistributionLogLikelihood(real sampled_value_real, real alpha, real beta) {
  //x^{a-1} * (1-x)^{b-1} / Beta(a, b)
  double loglikelihood = 0.0;
  loglikelihood += (alpha - 1.0) * log(sampled_value_real);
  loglikelihood += (beta - 1.0) * log(1.0 - sampled_value_real);
  loglikelihood -= gsl_sf_lnbeta(alpha, beta);
  return loglikelihood;
}

real PoissonDistributionLogLikelihood(int sampled_value_count, real lambda) {
  //l^k * e^{-l} / k!
  double loglikelihood = sampled_value_count * log(lambda);
  loglikelihood -= gsl_sf_lnfact(sampled_value_count);
  loglikelihood -= lambda;
  return loglikelihood;
}

real GammaDistributionLogLikelihood(real sampled_value_real, real alpha, real beta) {
  //b^a * x^{a-1} * e^{-b * x} / Gamma(a)
  if (sampled_value_real <= 0.0) {
    return log(0.0);
  }
  double loglikelihood = alpha * log(beta);
  loglikelihood += (alpha - 1.0) * log(sampled_value_real);
  loglikelihood -= beta * sampled_value_real;
  loglikelihood -= gsl_sf_lngamma(alpha);
  return loglikelihood;
}

real InverseGammaDistributionLogLikelihood(real sampled_value_real, real alpha, real beta) {
  //b^a * x^{-a-1} * e^{-b / x} / Gamma(a)
  double loglikelihood = alpha * log(beta);
  loglikelihood -= (alpha + 1.0) * log(sampled_value_real);
  loglikelihood -= beta / sampled_value_real;
  loglikelihood -= gsl_sf_lngamma(alpha);
  return loglikelihood;
}

real ChiSquaredDistributionLogLikelihood(real sampled_value_real, real nu) {
  //(x / 2)^{nu/2 - 1} * e^{-x/2} / (2 * Gamma(nu / 2))
  double loglikelihood = (0.5 * nu - 1.0) * log(0.5 * sampled_value_real);
  loglikelihood -= 0.5 * sampled_value_real;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  return loglikelihood;
}

real InverseChiSquaredDistributionLogLikelihood(real sampled_value_real, real nu) {
  //(2x)^{-nu/2 - 1} * e^{-1/2x} / (2 * Gamma(nu / 2))
  double loglikelihood = (-0.5 * nu  - 1.0) * log(2.0 * sampled_value_real);
  loglikelihood -= 0.5 / sampled_value_real;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  return loglikelihood;
}

