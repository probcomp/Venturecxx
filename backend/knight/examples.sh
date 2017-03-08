metaprob -e 'print(((x) -> { x })(2))' # 2
metaprob -e 'print(normal(2, 1))' # x where x ~ normal(2, 1)
metaprob -e 'print(get_current_trace())' # An empty trace
metaprob -e 'print(get_current_trace() has)' # False
metaprob -e '{ t = get_current_trace(); t := 5; print(@t) }' # 5
metaprob -e '{ t = T{ 6 }; print(@t) }' # 6

metaprob -e '{
  t = T{};
  (score, x) = regenerate(normal, [0, 1], T{}, t);
  print((score, x, @t)) }' # List(0, x, x) where x ~ normal(0, 1)

metaprob -e '{
  t2 = T{};
  (score, x) = regenerate(normal, [0, 1], T{1}, t2);
  print((score, x, @t2)) }' # List(-1.41, 1, 1)

metaprob -e '{
  t2 = T{1};
  (score, x) = regenerate(normal, [0, 1], T{}, t2);
  print((score, x, @t2)) }' # List(0, 1, 1)

# Running a synthetic SP
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e 'print(normal_normal(0, 1, 1))' # x where x ~ normal(0, 2)

# Tracing a synthetic SP
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  model = () ~> { normal_normal(0, 100, 1) };
  t2 = T{};
  regenerate(model, [], T{}, t2);
  subt = t2[0, "app"];
  print((@subt["x"], @subt))
}' # List(x, y) where x ~ normal(0, 100) and y ~ normal(x, 1)

# Constraining a synthetic SP
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  model = () ~> { normal_normal(0, 1, 1) };
  t1 = T{ *A/0/app/. = 5 };
  t2 = T{};
  (score, _) = regenerate(model, [], t1, t2);
  subt = t2[0, "app"];
  print((score, @subt["x"], @subt))
}' # List(-7.52, x, 5) where x ~ normal(2.5, 1/sqrt(2))

# Test generic regenerator_of
metaprob -e '{
  t2 = T{1};
  (score, x) = regenerate(sp(regenerator_of(normal)), [0, 1], T{}, t2);
  print((score, x, @t2)) }' # List(0, 1, 1)

# Test tracing a mechanism
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t2 = T{};
  t4 = T{};
  regenerate(regenerator_of(normal_normal), [[0, 1, 1], T{}, t2], T{}, t4);
  print((@t2["x"], t4))
}' # List(x, a trace) where x ~ normal(0, 1)

# Test another trace of a mechanism
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t2 = T{};
  t4 = T{};
  (out_score, (in_score, y)) = regenerate(regenerator_of(normal_normal), [[0, 1, 1], T{5}, t2], T{}, t4);
  print((out_score, in_score, y, @t2["x"], t4))
}' # List(0, -7.52, 5, x, a trace) where x ~ normal(2.5, 1/sqrt(2))

# Test intervening on a traced mechanism
# Compare the test case "constraining a synthetic SP"
metaprob -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t2 = T{};
  t4 = T{ *A/3/app/0/app/0/app/5/def/app/. = 7 };
  (out_score, (in_score, y)) = regenerate(regenerator_of(normal_normal), [[0, 1, 1], T{5}, t2], T{}, t4);
  print((out_score, in_score, y, @t2["x"], t4))
}' # List(0, -7.52, 5, 7, a trace)
