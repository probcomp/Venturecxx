# Here are the models

[ASSUME D 10]
[ASSUME sigma_2 1]

; Specific to non-Bayesian model
[ASSUME sigma_2_u 1]
[ASSUME sigma_2_v 1]
[ASSUME Sigma_u (scalar_mult sigma_2_u (id_matrix D))]
[ASSUME mu_u (repeat 0 D)]
[ASSUME Sigma_v (scalar_mult sigma_2_v (id_matrix D))]
[ASSUME mu_v (repeat 0 D)]

; Specific to Bayesian model
[ASSUME mu_0 (repeat 0 D)]
[ASSUME nu_0 D]
[ASSUME beta_0 1]
[ASSUME W_0 (id_matrix D)]
[ASSUME Sigma_u (inv_wishart W_0 nu_0)]
[ASSUME mu_u (multivariate_normal mu_0 (scalar_mult beta_0 Sigma_u))]
[ASSUME Sigma_v (inv_wishart W_0 nu_0)]
[ASSUME mu_v (multivariate_normal mu_0 (scalar_mult beta_0 Sigma_u))]

; Shared by both
[ASSUME make_U (mem (lambda (user) (multivariate_normal mu_u Sigma_u)))]
[ASSUME make_V (mem (lambda (movie) (multivariate_normal mu_v Sigma_v)))]
[ASSUME make_R (mem (lambda (user movie) (normal (vector_dot (make_U user) (make_V movie)) (sqrt sigma_2))))]