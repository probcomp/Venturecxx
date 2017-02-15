python -m venture.knight.driver -e '((x) -> { x })(2)' # (0, 2)
python -m venture.knight.driver -e 'normal(2, 1)' # (0, x) where x ~ normal(2, 1)
python -m venture.knight.driver -e 'get_current_trace()' # (0, An empty trace)
python -m venture.knight.driver -e 'trace_has(get_current_trace())' # (0, False)
python -m venture.knight.driver -e '{ t = get_current_trace(); _ = trace_set(t, 5); trace_get(t) }' # (0, 5)

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }' # (0, List(List(0 . x), x)) where x ~ normal(0, 1)

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  _ = trace_set(t1, 1);
  t2 = get_current_trace();
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }' # (0, List(List(-1.41 . 1), 1))

python -m venture.knight.driver -e '{
  t1 = get_current_trace();
  t2 = get_current_trace();
  _ = trace_set(t2, 1);
  res = regenerate(normal, [0, 1], t1, t2);
  list(res, trace_get(t2)) }' # (0, List(List(0 . 1), 1))
