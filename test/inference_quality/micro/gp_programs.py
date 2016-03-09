# a number of gp programs

simple_CxWN = """

  assume noise_sigma = tag("hyper", 0, uniform_continuous(0, 10));   

  assume wn = gp_cov_delta(0.000001);
  assume const = gp_cov_const(noise_sigma);
  assume cov = gp_cov_product(const,wn);

  assume gp = make_gp(zero, cov);
   """
simple_CplusCxWN = """

  assume noise_sigma = tag("hyper", 0, uniform_continuous(0, 10));   
  assume mean_line = tag("hyper", 1, uniform_continuous(0, 10));   

  assume wn = gp_cov_delta(0.000001);
  assume scale = gp_cov_const(noise_sigma);
  assume const = gp_cov_const(mean_line);
  assume cov = gp_cov_sum(const,gp_cov_product(scale,wn));

  assume gp = make_gp(zero, cov);
   """

simple_periodic = """

  assume p = tag("hyper", 0, uniform_continuous(0, 100)); 
  assume t = tag("hyper", 1, uniform_continuous(0, 100));   
 
  assume per = gp_cov_periodic(p, t);

  assume gp = make_gp(zero, per);

   """
simple_CxPER = """

  assume p = tag("hyper", 0, uniform_continuous(0, 10)); 
  assume t = tag("hyper", 1, uniform_continuous(0, 10));   
  assume c = tag("hyper", 2, uniform_continuous(0, 10));   

  assume per = gp_cov_periodic(p, t);
  assume const = gp_cov_const(c);
  assume cov = gp_cov_product(const,per);

  assume gp = make_gp(zero, cov);

   """

simple_se =  """
  
  assume se = gp_cov_se(uniform_continuous(0, 5));

  assume gp = make_gp(zero, se);

  """


simple_constant = """

  assume c = tag("hyper", 0, uniform_continuous(0, 10));   

  assume cov = gp_cov_const(c);

  assume gp = make_gp(zero, cov);

   """
