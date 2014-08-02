/*
 * mvnorm.cpp
 *
 *  Created on: Apr 1, 2011
 *      Author: pickrell
 */

#include "sps/silva_mvn.h"

/*****************************************************************************************************************/
/*****************************************************************************************************************/
int rmvnorm(const gsl_rng *r, const int n, const gsl_vector *mean, const gsl_matrix *var, gsl_vector *result){
/* multivariate normal distribution random number generator */
/*
*	n	dimension of the random vetor
*	mean	vector of means of size n
*	var	variance matrix of dimension n x n
*	result	output variable with a sigle random vector normal distribution generation
*/
int k;
gsl_matrix *work = gsl_matrix_alloc(n,n);

gsl_matrix_memcpy(work,var);
gsl_linalg_cholesky_decomp(work);

for(k=0; k<n; k++)
	gsl_vector_set( result, k, gsl_ran_ugaussian(r) );

gsl_blas_dtrmv(CblasLower, CblasNoTrans, CblasNonUnit, work, result);
gsl_vector_add(result,mean);

gsl_matrix_free(work);

return 0;
}

/*****************************************************************************************************************/
/*****************************************************************************************************************/
double dmvnorm(const int n, const gsl_vector *x, const gsl_vector *mean, const gsl_matrix *var){
/* multivariate normal density function    */
/* LOGGED
*	n	dimension of the random vetor
*	mean	vector of means of size n
*	var	variance matrix of dimension n x n
*/
int s;
double ax,ay;
gsl_vector *ym, *xm;
gsl_matrix *work = gsl_matrix_alloc(n,n),
           *winv = gsl_matrix_alloc(n,n);
gsl_permutation *p = gsl_permutation_alloc(n);

gsl_matrix_memcpy( work, var );
gsl_linalg_LU_decomp( work, p, &s );
gsl_linalg_LU_invert( work, p, winv );

//for (int i = 0; i < n ; i++){
//	std::cout << gsl_vector_get(x, i) << " "<< gsl_vector_get(mean, i)<< "\n";
//}
//for (int i = 0; i < n ; i++){
//	for(int j = 0; j < n ; j++){
//		std::cout << gsl_matrix_get(work, i,j) << " ";
//	}
//	std::cout << "\n";
//}
//ax = gsl_linalg_LU_lndet( work, s );
ax = gsl_linalg_LU_lndet( work);
//std::cout << "in dmvnorm "<< ax << "\n";
gsl_matrix_free( work );
gsl_permutation_free( p );

xm = gsl_vector_alloc(n);
gsl_vector_memcpy( xm, x);
gsl_vector_sub( xm, mean );
ym = gsl_vector_alloc(n);
gsl_blas_dsymv(CblasUpper,1.0,winv,xm,0.0,ym);
gsl_matrix_free( winv );
gsl_blas_ddot( xm, ym, &ay);
gsl_vector_free(xm);
gsl_vector_free(ym);
//std::cout << ay << " "<< ax << "\n";
ay = -0.5*ay - 0.5* (log(pow((2*M_PI),n))+ ax);
//ay = exp(-0.5*ay)/sqrt( pow((2*M_PI),n)*ax );
//std::cout << ay << "\n";
return ay;
}

/*****************************************************************************************************************/
/*****************************************************************************************************************/
int rmvt(const gsl_rng *r, const int n, const gsl_vector *location, const gsl_matrix *scale, const int dof, gsl_vector *result){
/* multivariate Student t distribution random number generator */
/*
*	n	 dimension of the random vetor
*	location vector of locations of size n
*	scale	 scale matrix of dimension n x n
*	dof	 degrees of freedom
*	result	 output variable with a single random vector normal distribution generation
*/
int k;
gsl_matrix *work = gsl_matrix_alloc(n,n);
double ax = 0.5*dof;

ax = gsl_ran_gamma(r,ax,(1/ax));     /* gamma distribution */

gsl_matrix_memcpy(work,scale);
gsl_matrix_scale(work,(1/ax));       /* scaling the matrix */
gsl_linalg_cholesky_decomp(work);

for(k=0; k<n; k++)
	gsl_vector_set( result, k, gsl_ran_ugaussian(r) );

gsl_blas_dtrmv(CblasLower, CblasNoTrans, CblasNonUnit, work, result);
gsl_vector_add(result, location);

gsl_matrix_free(work);

return 0;
}

/*****************************************************************************************************************/
/*****************************************************************************************************************/
double dmvt(const int n, const gsl_vector *x, const gsl_vector *location, const gsl_matrix *scale, const int dof){
/* multivariate Student t density function */
/*
*	n	 dimension of the random vetor
*	location vector of locations of size n
*	scale	 scale matrix of dimension n x n
*	dof	 degrees of freedom
*/
int s;
double ax,ay,az=0.5*(dof + n);
gsl_vector *ym, *xm;
gsl_matrix *work = gsl_matrix_alloc(n,n),
           *winv = gsl_matrix_alloc(n,n);
gsl_permutation *p = gsl_permutation_alloc(n);

gsl_matrix_memcpy( work, scale );
gsl_linalg_LU_decomp( work, p, &s );
gsl_linalg_LU_invert( work, p, winv );
ax = gsl_linalg_LU_det( work, s );
gsl_matrix_free( work );
gsl_permutation_free( p );

xm = gsl_vector_alloc(n);
gsl_vector_memcpy( xm, x);
gsl_vector_sub( xm, location );
ym = gsl_vector_alloc(n);
gsl_blas_dsymv(CblasUpper,1.0,winv,xm,0.0,ym);
gsl_matrix_free( winv );
gsl_blas_ddot( xm, ym, &ay);
gsl_vector_free(xm);
gsl_vector_free(ym);

ay = pow((1+ay/dof),-az)*gsl_sf_gamma(az)/(gsl_sf_gamma(0.5*dof)*sqrt( pow((dof*M_PI),n)*ax ));

return ay;
}
