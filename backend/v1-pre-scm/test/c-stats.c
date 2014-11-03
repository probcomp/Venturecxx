#include "scheme.h"
#include "prims.h"

#include <gsl/gsl_cdf.h>
#include <gsl/gsl_randist.h>

DEFINE_PRIMITIVE ("GSL_CDF_CHISQ_Q", Prim_gsl_cdf_chisq_Q, 2, 2, "(X NU)")
{
  double x, nu, result;
  PRIMITIVE_HEADER (2);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  nu = (arg_real_number (2));

  result = (gsl_cdf_chisq_Q (x, nu));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

DEFINE_PRIMITIVE ("GSL_CDF_GAUSSIAN_P", Prim_gsl_cdf_gaussian_P, 2, 2, "(X SIGMA)")
{
  double x, sigma, result;
  PRIMITIVE_HEADER (2);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  sigma = (arg_real_number (2));

  result = (gsl_cdf_gaussian_P (x, sigma));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

DEFINE_PRIMITIVE ("GSL_RAN_GAMMA_PDF", Prim_gsl_ran_gamma_pdf, 3, 3, "(X ALPHA BETA)")
{
  double x, alpha, beta, result;
  PRIMITIVE_HEADER (3);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  alpha = (arg_real_number (2));
  beta = (arg_real_number (3));

  result = (gsl_ran_gamma_pdf (x, alpha, beta));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

DEFINE_PRIMITIVE ("GSL_CDF_GAMMA_P", Prim_gsl_cdf_gamma_P, 3, 3, "(X ALPHA BETA)")
{
  double x, alpha, beta, result;
  PRIMITIVE_HEADER (3);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  alpha = (arg_real_number (2));
  beta = (arg_real_number (3));

  result = (gsl_cdf_gamma_P (x, alpha, beta));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

#ifdef COMPILE_AS_MODULE

const char *
dload_initialize_file (void)
{
  declare_primitive ("GSL_CDF_CHISQ_Q", Prim_gsl_cdf_chisq_Q, 2, 2, "(X NU)");
  declare_primitive ("GSL_CDF_GAUSSIAN_P", Prim_gsl_cdf_gaussian_P, 2, 2, "(X SIGMA)");
  declare_primitive ("GSL_RAN_GAMMA_PDF", Prim_gsl_ran_gamma_pdf, 3, 3, "(X ALPHA BETA)");
  declare_primitive ("GSL_CDF_GAMMA_P", Prim_gsl_cdf_gamma_P, 3, 3, "(X ALPHA BETA)");
  return "#prgslstats";
}

#endif
