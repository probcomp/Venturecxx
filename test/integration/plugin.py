import venture.lite.value as v

def __venture_start__(r):
  r.bind_callback("foo", lambda _inferrer: None)
  return v.VentureNumber(7) # To test that load_plugin will forward the return value
