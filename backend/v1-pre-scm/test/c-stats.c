// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#include "scheme.h"
#include "prims.h"

#include <gsl/gsl_cdf.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf_gamma.h>

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

DEFINE_PRIMITIVE ("GSL_SF_LNGAMMA", Prim_gsl_sf_lngamma, 1, 1, "(X)")
{
  double x, result;
  PRIMITIVE_HEADER (1);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */

  result = (gsl_sf_lngamma (x));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

DEFINE_PRIMITIVE ("GSL_RAN_GAMMA_PDF", Prim_gsl_ran_gamma_pdf, 3, 3, "(X SHAPE THETA)")
{
  double x, shape, theta, result;
  PRIMITIVE_HEADER (3);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  shape = (arg_real_number (2));
  theta = (arg_real_number (3));

  result = (gsl_ran_gamma_pdf (x, shape, theta));

  /*
   * Can't allocate resources (e.g., malloc) in frobnitz.  Ask me how
   * if you want to do that.
   */

  /* Use PRIMITIVE_RETURN, not return.  */
  PRIMITIVE_RETURN (double_to_flonum (result));
}

DEFINE_PRIMITIVE ("GSL_CDF_GAMMA_P", Prim_gsl_cdf_gamma_P, 3, 3, "(X SHAPE THETA)")
{
  double x, shape, theta, result;
  PRIMITIVE_HEADER (3);

  x  = (arg_real_number (1));     /* Argument numbering starts at 1.  */
  shape = (arg_real_number (2));
  theta = (arg_real_number (3));

  result = (gsl_cdf_gamma_P (x, shape, theta));

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
  declare_primitive ("GSL_SF_LNGAMMA", Prim_gsl_sf_lngamma, 1, 1, "(X)");
  declare_primitive ("GSL_RAN_GAMMA_PDF", Prim_gsl_ran_gamma_pdf, 3, 3, "(X SHAPE THETA)");
  declare_primitive ("GSL_CDF_GAMMA_P", Prim_gsl_cdf_gamma_P, 3, 3, "(X SHAPE THETA)");
  return "#prgslstats";
}

#endif
