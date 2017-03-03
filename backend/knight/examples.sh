python -m venture.knight.driver -e '((x) -> { x })(2)' # (0, 2)
python -m venture.knight.driver -e 'normal(2, 1)' # (0, x) where x ~ normal(2, 1)
python -m venture.knight.driver -e 'get_current_trace()' # (0, An empty trace)
python -m venture.knight.driver -e 'trace_has(get_current_trace())' # (0, False)
python -m venture.knight.driver -e '{ t = get_current_trace(); t := 5; @t }' # (0, 5)

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, @t2) }' # (0, List(List(0 . x), x)) where x ~ normal(0, 1)

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t1 := 1;
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, @t2) }' # (0, List(List(-1.41 . 1), 1))

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  t2 := 1;
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, @t2) }' # (0, List(List(0 . 1), 1))

# Running a synthetic SP
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e 'normal_normal(0, 1, 1)' # (0, x) where x ~ normal(0, 2)

# Tracing a synthetic SP
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  model = () ~> { normal_normal(0, 100, 1) };
  t1 = get_current_trace();
  t2 = get_current_trace();
  regenerate(model, [], t1, t2);
  subt = t2[0, "app"];
  list(@subt["x"], @subt)
}' # (0, List(x, y)) where x ~ normal(0, 100) and y ~ normal(x, 1)

# Constraining a synthetic SP
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  model = () ~> { normal_normal(0, 1, 1) };
  t1 = get_current_trace();
  t1[0, "app"] := 5;
  t2 = get_current_trace();
  res = regenerate(model, [], t1, t2);
  subt = t2[0, "app"];
  list(first(res), @subt["x"], @subt)
}' # (0, List(-7.52, x, 5)) where x ~ normal(2.5, 1/sqrt(2))

# Test generic regenerator_of
python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  t2 := 1;
  res = regenerate(sp(regenerator_of(normal)), [0, 1], t1, t2);
  list(res, @t2) }' # (0, List(List(0 . 1), 1))

# Test tracing a mechanism
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  t3 = get_current_trace();
  t4 = get_current_trace();
  regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(@t2["x"], t4)
}' # (0, List(x, a trace)) where x ~ normal(0, 1)

# Test another trace of a mechanism
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  t1 := 5;
  t3 = get_current_trace();
  t4 = get_current_trace();
  res = regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(res, @t2["x"], t4)
}' # (0, List(List(0, -7.52 . 5), x, a trace)) where x ~ normal(2.5, 1/sqrt(2))

# Test intervening on a traced mechanism
# Compare the test case "constraining a synthetic SP"
python -m venture.knight.driver -f backend/knight/prelude.vnts -f backend/knight/normal-normal.vnts \
  -e '{
  t1 = get_current_trace();
  t1 := 5;
  t2 = get_current_trace();
  t3 = get_current_trace();
  t4 = get_current_trace();
  t4[3, "app", 0, "app", 0, "app", 6, "def", "app"] := 7;
  res = regenerate(regenerator_of(normal_normal), [[0, 1, 1], t1, t2], t3, t4);
  list(res, @t2["x"], t4)
}' # (0, List(List(0, -7.52 . 5), 7, a trace))
