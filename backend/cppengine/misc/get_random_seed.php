<?

  function openssl_random_pseudo_bytes($length) {
    $length_n = (int) $length; // shell injection is no fun
    $handle = popen("/usr/bin/openssl rand $length_n", "r");
    $data = stream_get_contents($handle);
    pclose($handle);
    return $data;
  }

  function get_random_int() {
    $a = ((microtime(true) * 100) % 10000) * 10000;
    $b = hexdec(bin2hex(openssl_random_pseudo_bytes(2)));
    return $a + $b;
  }
  echo get_random_int();


?>