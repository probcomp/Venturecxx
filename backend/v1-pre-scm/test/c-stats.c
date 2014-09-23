#include "scheme.h"
#include "prims.h"

#include <gsl/gsl_cdf.h>

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

#ifdef COMPILE_AS_MODULE

const char *
dload_initialize_file (void)
{
  declare_primitive ("GSL_CDF_CHISQ_Q", Prim_gsl_cdf_chisq_Q, 2, 2, "(X NU)");
  declare_primitive ("GSL_CDF_GAUSSIAN_P", Prim_gsl_cdf_gaussian_P, 2, 2, "(X SIGMA)");
  return "#prgslstats";
}

#endif
