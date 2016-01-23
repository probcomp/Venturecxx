import pystan
import numpy as np
import pandas as pd

# Try to learn a mixture model on Apogee, Perigee.

kepler_code = """
functions {
  real kepler(real apogee_km, real perigee_km) {
    real GM; real EARTH_RADIUS; real PI; real sma;
    GM <- 398600.4418;
    EARTH_RADIUS <- 6378;
    PI <- 3.14158;
    sma <- 0.5*(fabs(apogee_km) + fabs(perigee_km)) + 6378;
    return 2 * PI * sqrt(pow(sma,3)/GM) / 60.;
  }
}
data {
    int<lower=1> K;         // Number of mixture mixture components
    int<lower=1> N;         // Number of observations.
    real y[N];              // Fake data in R
    int z[N];               // Cluster assignment (coming from Venture).
}
parameters {
  simplex[K] theta;           // Mixture weights.
  real mu[K];                 // Locations of mixture components.
  real<lower=0.1> sigma[K];   // Scale of mixture components.
}
model {
    int c;
    for (k in 1:K) {
      sigma[k] ~ inv_gamma(1, 20);
      mu[k] ~ normal(15000, 5000);
    }
    for (n in 1:N) {
        c <- z[n] + 1;
        increment_log_prob(
          log(theta[c]) + normal_log(y[n], mu[c], sigma[c]));
    }
}
"""

satellites = pd.read_csv('resources/satellites.csv').dropna()
y = np.asarray(satellites[['Apogee_km','Perigee_km']])
# t = np.asarray(satellites['Period_minutes'])
z = np.loadtxt('resources/clusters.txt', delimiter=',')

kepler_data = {
  'K': len(set(z)),
  'N': len(y),
  'y': y[:,0],
  'z': z,
  }

fit = pystan.stan(model_code=kepler_code, data=kepler_data, iter=25000,
  chains=1, verbose=True)

print fit

# if matplotlib is installed (optional, not required), a visual summary and
# traceplot are available
fit.plot()
